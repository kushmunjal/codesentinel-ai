import pytest
from unittest.mock import MagicMock
from codesentinel.schemas import Finding
from codesentinel.review.sarif import generate_sarif, write_sarif
from codesentinel.review.checks_api import create_check_run

def test_generate_sarif():
    findings = [
        Finding(
            file="auth.py",
            line=42,
            severity="critical",
            category="security",
            explanation="Hardcoded credential found.",
            suggested_fix="os.environ.get('SECRET')"
        ),
        Finding(
            file="utils.py",
            line=10,
            severity="low",
            category="style",
            explanation="Unused variable.",
            suggested_fix=None
        )
    ]

    sarif = generate_sarif(findings)
    assert sarif["version"] == "2.1.0"
    assert "$schema" in sarif
    assert len(sarif["runs"]) == 1

    run = sarif["runs"][0]
    assert run["tool"]["driver"]["name"] == "CodeSentinel AI"
    assert len(run["results"]) == 2

    # Check mapping
    res_crit = run["results"][0]
    assert res_crit["ruleId"] == "codesentinel/security"
    assert res_crit["level"] == "error"
    assert res_crit["locations"][0]["physicalLocation"]["artifactLocation"]["uri"] == "auth.py"
    assert res_crit["locations"][0]["physicalLocation"]["region"]["startLine"] == 42
    assert "fixes" in res_crit

    res_low = run["results"][1]
    assert res_low["ruleId"] == "codesentinel/style"
    assert res_low["level"] == "note"

def test_create_check_run():
    mock_client = MagicMock()
    mock_client.token = "test-token"
    mock_resp = MagicMock()
    mock_resp.status_code = 201
    mock_resp.json.return_value = {"id": 12345, "status": "completed"}
    mock_client.session.post.return_value = mock_resp

    findings = [
        Finding(
            file="main.py",
            line=5,
            severity="high",
            category="security",
            explanation="Vulnerable eval call.",
            suggested_fix=None
        )
    ]

    result = create_check_run(
        mock_client,
        owner="test-owner",
        repo="test-repo",
        head_sha="abcdef123456",
        name="CodeSentinel AI Review",
        findings=findings
    )

    assert result["id"] == 12345
    mock_client.session.post.assert_called_once()
    call_args = mock_client.session.post.call_args
    url = call_args[0][0]
    json_body = call_args[1]["json"]
    assert "check-runs" in url
    assert json_body["head_sha"] == "abcdef123456"
    assert json_body["conclusion"] == "failure"
    assert len(json_body["output"]["annotations"]) == 1
    assert json_body["output"]["annotations"][0]["annotation_level"] == "failure"
