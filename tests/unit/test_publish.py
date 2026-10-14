from unittest.mock import MagicMock

import pytest
from requests import HTTPError

from codesentinel.review.publish import publish_review, publish_summary
from codesentinel.schemas import ChangeGroup, PRSummary


def test_publish_summary_new_comment():
    client = MagicMock()
    mock_get_resp = MagicMock()
    mock_get_resp.json.return_value = [
        {"id": 101, "body": "Regular user comment"}
    ]
    client.get.return_value = mock_get_resp
    
    summary = PRSummary(
        summary="Add auth middleware",
        risk_level="high",
        risk_reasoning="Changes authentication validation logic",
        change_groups=[
            ChangeGroup(name="Auth", description="Added JWT authentication middleware")
        ],
        review_effort=3,
        review_effort_reasoning="Standard auth refactor",
        breaking_change_suspected=True,
        breaking_change_reasoning="Removed deprecated legacy token header",
        guideline_violations=["Missing docstring on authenticate()"]
    )
    
    context = {
        "ready_to_merge_text": "No - Open high/critical findings.",
        "findings_stats": {
            "counts_str": "1 high, 2 low",
            "top_concerns": ["[HIGH] SQL Injection risk in auth.py"]
        },
        "has_security_findings": True,
        "tests_missing": True,
        "dependency_changes": ["Added in package.json: jsonwebtoken@9.0.0"],
        "suggested_reviewers": ["security-team", "alice"],
        "linked_issues": [{"number": 42, "title": "Implement JWT auth"}]
    }
    
    publish_summary(client, "owner", "repo", 7, summary, context, commit_id="abc1234")
    
    # Verify POST was called for new comment
    client.session.post.assert_called_once()
    args, kwargs = client.session.post.call_args
    assert "https://api.github.com/repos/owner/repo/issues/7/comments" in args[0]
    body = kwargs["json"]["body"]
    assert "<!-- codesentinel:summary -->" in body
    assert "<!-- codesentinel:last_sha=abc1234 -->" in body
    assert "**Risk:** High" in body
    assert "Changes authentication validation logic" in body
    assert "**Ready to Merge:** No - Open high/critical findings." in body
    assert "Added JWT authentication middleware" in body
    assert "1 high, 2 low" in body
    assert "[HIGH] SQL Injection risk" in body
    assert "SECURITY FINDINGS DETECTED" in body
    assert "Source logic changed with ZERO matching test changes" in body
    assert "Possible Breaking Change" in body
    assert "jsonwebtoken@9.0.0" in body
    assert "Missing docstring on authenticate()" in body
    assert "**Review Effort:** 3/5" in body
    assert "@security-team, @alice" in body
    assert "Resolves #42: Implement JWT auth" in body
    assert "http://127.0.0.1:8080" in body

def test_publish_summary_update_existing_comment():
    client = MagicMock()
    mock_get_resp = MagicMock()
    mock_get_resp.json.return_value = [
        {"id": 101, "body": "Regular user comment"},
        {"id": 202, "body": "<!-- codesentinel:summary -->\nOld summary"}
    ]
    client.get.return_value = mock_get_resp
    
    summary = PRSummary(
        summary="Refactor logging",
        risk_level="low",
        risk_reasoning="Safe logging updates",
        change_groups=[],
        review_effort=1,
        review_effort_reasoning="Minor change",
        breaking_change_suspected=False,
        guideline_violations=[]
    )
    
    context = {
        "ready_to_merge_text": "Yes",
        "tests_missing": False,
        "has_security_findings": False,
        "findings_stats": {}
    }
    
    publish_summary(client, "owner", "repo", 7, summary, context, commit_id="def5678")
    
    # Verify PATCH was called on existing comment id 202
    client.session.patch.assert_called_once()
    args, kwargs = client.session.patch.call_args
    assert "https://api.github.com/repos/owner/repo/issues/comments/202" in args[0]
    body = kwargs["json"]["body"]
    assert "<!-- codesentinel:summary -->" in body
    assert "Test Coverage:** Satisfactory." in body
    client.session.post.assert_not_called()

def test_publish_review_success():
    client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.ok = True
    client.session.post.return_value = mock_resp
    
    comments = [
        {"path": "src/main.py", "line": 10, "side": "RIGHT", "body": "Fix this bug"}
    ]
    publish_review(client, "owner", "repo", 15, "commit123", comments)
    
    client.session.post.assert_called_once_with(
        "https://api.github.com/repos/owner/repo/pulls/15/reviews",
        json={"commit_id": "commit123", "event": "COMMENT", "comments": comments}
    )

def test_publish_review_error_raises():
    client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.ok = False
    mock_resp.text = "Unprocessable Entity"
    mock_resp.raise_for_status.side_effect = HTTPError("422 Client Error")
    client.session.post.return_value = mock_resp
    
    with pytest.raises(HTTPError):
        publish_review(client, "owner", "repo", 15, "commit123", [])
