import json
import os
from unittest.mock import MagicMock, patch

import pytest

from codesentinel.api.database import IssueState, SessionLocal
from codesentinel.review.pipeline import run_pipeline
from codesentinel.schemas import (
    ChangeGroup,
    Finding,
    PRSummary,
    ReviewResult,
    TriageResult,
)
from codesentinel.triage.pipeline import run_triage_pipeline


@pytest.fixture
def mock_fixtures():
    base_dir = os.path.dirname(__file__)
    fixtures_dir = os.path.join(base_dir, "..", "fixtures")
    
    with open(os.path.join(fixtures_dir, "mock_pr_diff.diff"), "r") as f:
        diff_text = f.read()
        
    with open(os.path.join(fixtures_dir, "mock_github_data.json"), "r") as f:
        gh_data = json.load(f)
        
    return {
        "diff": diff_text,
        "github": gh_data
    }

def test_full_review_pipeline_end_to_end(mock_fixtures, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    os.environ["ACTION_PATH"] = "/home/student/worktrees/ws-qa"
    
    gh_data = mock_fixtures["github"]
    raw_diff = mock_fixtures["diff"]
    
    # 1. Mock GitHub Client
    mock_gh = MagicMock()
    mock_gh.get_pr_diff.return_value = raw_diff
    def mock_file_content(owner, repo, path, ref="main"):
        if "CODEOWNERS" in path:
            return gh_data["codeowners"]
        return None
    mock_gh.get_file_content.side_effect = mock_file_content
    
    # PR details response
    pr_resp = MagicMock()
    pr_resp.json.return_value = gh_data["pr"]
    
    # Comments response (no existing comments)
    comments_resp = MagicMock()
    comments_resp.json.return_value = []
    
    mock_gh.get.side_effect = lambda url, **kwargs: (
        pr_resp if "/pulls/" in url else comments_resp
    )
    mock_gh.get_issue.return_value = gh_data["linked_issue"]
    
    # Session mocks
    post_review_resp = MagicMock()
    post_review_resp.ok = True
    mock_gh.session.post.return_value = post_review_resp
    
    # 2. Mock LLM responses
    mock_finding = Finding(
        file="src/api.py",
        line=6,
        severity="high",
        category="security",
        explanation="SQL injection detected in string formatting query",
        suggested_fix="db.execute('SELECT * FROM items WHERE name = %s', (q,))"
    )
    mock_review_result = ReviewResult(findings=[mock_finding])
    
    mock_summary = PRSummary(
        summary="Adds a search endpoint with security flaw",
        risk_level="high",
        risk_reasoning="Critical SQL injection risk in query construction",
        change_groups=[
            ChangeGroup(name="Core logic", description="Added search endpoint in src/api.py"),
            ChangeGroup(name="Dependencies", description="Added axios in package.json")
        ],
        review_effort=3,
        review_effort_reasoning="Endpoint needs security parameterization and unit tests",
        breaking_change_suspected=False,
        guideline_violations=[]
    )
    
    def mock_llm_generate(sys_p, usr_p, schema):
        if schema == ReviewResult:
            return mock_review_result
        elif schema == PRSummary:
            return mock_summary
        raise ValueError(f"Unexpected schema: {schema}")
        
    with patch("codesentinel.review.pipeline.GitHubClient", return_value=mock_gh), \
         patch("codesentinel.review.pipeline.OpenAICompatProvider") as mock_provider_cls:
        
        mock_provider_instance = MagicMock()
        mock_provider_instance.generate.side_effect = mock_llm_generate
        mock_provider_cls.return_value = mock_provider_instance
        
        # Execute review pipeline
        run_pipeline(owner="acme", repo="service", pr_number=42)
        
    # Verify outputs
    # 1. Dashboard file generated
    assert os.path.exists("dashboard/latest_review.json")
    with open("dashboard/latest_review.json") as f:
        review_output = json.load(f)
    assert review_output["summary"]["risk_level"] == "high"
    assert len(review_output["findings"]) == 1
    assert review_output["findings"][0]["file"] == "src/api.py"
    
    # 2. Summary comment published
    summary_calls = [c for c in mock_gh.session.post.call_args_list if "issues/42/comments" in c[0][0]]
    assert len(summary_calls) == 1
    summary_body = summary_calls[0][1]["json"]["body"]
    assert "<!-- codesentinel:summary -->" in summary_body
    assert "SQL injection detected" in summary_body
    assert "SECURITY FINDINGS DETECTED" in summary_body
    assert "core-team" in summary_body
    assert "backend-lead" in summary_body
    assert "Resolves #101" in summary_body

    # 3. Inline review comments published
    review_calls = [c for c in mock_gh.session.post.call_args_list if "pulls/42/reviews" in c[0][0]]
    assert len(review_calls) == 1
    review_payload = review_calls[0][1]["json"]
    assert review_payload["commit_id"] == "c0ffee1234567890abcdef"
    assert review_payload["event"] == "COMMENT"
    assert len(review_payload["comments"]) == 1
    assert review_payload["comments"][0]["path"] == "src/api.py"
    assert review_payload["comments"][0]["line"] == 6

def test_full_triage_pipeline_end_to_end(mock_fixtures, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    os.environ["ACTION_PATH"] = "/home/student/worktrees/ws-qa"
    
    gh_data = mock_fixtures["github"]
    
    mock_gh = MagicMock()
    mock_gh.get_issue.return_value = {
        "number": 101,
        "title": "SQL Injection in search API",
        "body": "User input in src/api.py is concatenated directly into SQL statement."
    }
    mock_gh.get_labels.return_value = gh_data["labels"]
    mock_gh.get_issues.return_value = gh_data["recent_issues"]
    def mock_file_content(owner, repo, path, ref="main"):
        if "CODEOWNERS" in path:
            return gh_data["codeowners"]
        if "README" in path:
            return "CodeSentinel API search Documentation"
        return None
    mock_gh.get_file_content.side_effect = mock_file_content
    
    mock_triage_result = TriageResult(
        type="Bug",
        priority="high",
        classification_reasoning="Security issue in search input validation",
        labels=["bug", "security"],
        duplicate_of=None,
        duplicate_reasoning=None,
        missing_info_specific=[],
        suggested_reply="Thank you for reporting this vulnerability. Our security team will review it."
    )
    
    with patch("codesentinel.triage.pipeline.GitHubClient", return_value=mock_gh), \
         patch("codesentinel.triage.pipeline.OpenAICompatProvider") as mock_provider_cls:
        
        mock_provider_instance = MagicMock()
        mock_provider_instance.generate.return_value = mock_triage_result
        mock_provider_cls.return_value = mock_provider_instance
        
        # Execute triage pipeline
        run_triage_pipeline(owner="acme", repo="service", issue_number=101)
        
    # Verify outputs
    # 1. Labels added to issue
    mock_gh.add_labels_to_issue.assert_called_once_with(
        "acme", "service", 101, ["bug", "security"]
    )
    
    # 2. Triage comment added
    mock_gh.add_comment_to_issue.assert_called_once()
    comment_args = mock_gh.add_comment_to_issue.call_args[0]
    assert comment_args[0] == "acme"
    assert comment_args[1] == "service"
    assert comment_args[2] == 101
    assert "CodeSentinel AI Triage" in comment_args[3]
    assert "high priority" in comment_args[3]
    assert "backend-lead" in comment_args[3]
    
    # 3. Dashboard file saved
    assert os.path.exists("dashboard/latest_triage.json")
    with open("dashboard/latest_triage.json") as f:
        triage_output = json.load(f)
    assert triage_output["title"] == "SQL Injection in search API"
    assert "bug" in triage_output["labels"]
    
    # 4. Database record verified
    db = SessionLocal()
    saved_issue = db.query(IssueState).filter(IssueState.number == 101).first()
    assert saved_issue is not None
    assert saved_issue.status == "Triaged"
    assert saved_issue.priority == "High"
    assert saved_issue.auto_type == "bug"
    db.close()

def test_full_review_pipeline_clean_pr(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    os.environ["ACTION_PATH"] = "/home/student/worktrees/ws-qa"
    
    clean_diff = """diff --git a/src/math_utils.py b/src/math_utils.py
--- a/src/math_utils.py
+++ b/src/math_utils.py
@@ -1,2 +1,4 @@
 def add(a: int, b: int) -> int:
     return a + b
+def multiply(a: int, b: int) -> int:
+    return a * b
diff --git a/tests/test_math_utils.py b/tests/test_math_utils.py
--- a/tests/test_math_utils.py
+++ b/tests/test_math_utils.py
@@ -1,2 +1,4 @@
 def test_add():
     assert add(1, 2) == 3
+def test_multiply():
+    assert multiply(2, 3) == 6
"""
    mock_gh = MagicMock()
    mock_gh.get_pr_diff.return_value = clean_diff
    mock_gh.get_file_content.return_value = None
    
    pr_resp = MagicMock()
    pr_resp.json.return_value = {
        "number": 55,
        "title": "Add multiplication helper",
        "body": "Implements multiply() with tests.",
        "draft": False,
        "head": {"sha": "11223344556677889900"}
    }
    comments_resp = MagicMock()
    comments_resp.json.return_value = []
    
    mock_gh.get.side_effect = lambda url, **kwargs: (
        pr_resp if "/pulls/" in url else comments_resp
    )
    
    clean_review = ReviewResult(findings=[])
    clean_summary = PRSummary(
        summary="Adds multiply utility function with tests",
        risk_level="low",
        risk_reasoning="Pure helper functions with unit test coverage",
        change_groups=[
            ChangeGroup(name="Core logic", description="Added multiply function"),
            ChangeGroup(name="Tests", description="Added test_multiply")
        ],
        review_effort=1,
        review_effort_reasoning="Well tested small change",
        breaking_change_suspected=False,
        guideline_violations=[]
    )
    
    def mock_llm(sys_p, usr_p, schema):
        if schema == ReviewResult:
            return clean_review
        elif schema == PRSummary:
            return clean_summary
        raise ValueError(f"Unexpected schema: {schema}")
        
    with patch("codesentinel.review.pipeline.GitHubClient", return_value=mock_gh), \
         patch("codesentinel.review.pipeline.OpenAICompatProvider") as mock_provider_cls:
        
        mock_provider_instance = MagicMock()
        mock_provider_instance.generate.side_effect = mock_llm
        mock_provider_cls.return_value = mock_provider_instance
        
        run_pipeline(owner="acme", repo="service", pr_number=55)
        
    # Check that summary was published with Ready to Merge: Yes
    summary_calls = [c for c in mock_gh.session.post.call_args_list if "issues/55/comments" in c[0][0]]
    assert len(summary_calls) == 1
    body = summary_calls[0][1]["json"]["body"]
    assert "**Ready to Merge:** Yes" in body
    assert "Test Coverage:** Satisfactory" in body
    
    # Review comments should NOT be published because there are no findings
    review_calls = [c for c in mock_gh.session.post.call_args_list if "pulls/55/reviews" in c[0][0]]
    assert len(review_calls) == 0
