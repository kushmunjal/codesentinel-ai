import pytest
import os
import time
from unittest.mock import MagicMock, patch
from pydantic import BaseModel
from codesentinel.review.publish import is_review_submitted, publish_review
from codesentinel.triage.pipeline import compute_body_hash, is_issue_already_triaged
from codesentinel.llm.openai_compat import OpenAICompatProvider
from codesentinel.llm.retry import generate_with_retry
from codesentinel.schemas import PRSummary

class DummySchema(BaseModel):
    message: str

def test_dependabot_missing_api_key_pipeline():
    """Verify run_pipeline safely exits neutral when API_KEY is missing or empty."""
    from codesentinel.review.pipeline import run_pipeline
    
    orig_api_key = os.environ.get("API_KEY")
    if "API_KEY" in os.environ:
        del os.environ["API_KEY"]

    try:
        mock_client = MagicMock()
        mock_client.token = "test-token"
        
        with patch("codesentinel.review.pipeline.GitHubClient", return_value=mock_client):
            # Must return without raising ValueError or unhandled exceptions
            run_pipeline("test-owner", "test-repo", 123)
            # Should have posted skipped review comment
            mock_client.add_comment_to_issue.assert_called_once()
            call_args = mock_client.add_comment_to_issue.call_args
            assert "Automated review skipped" in call_args[0][3]
    finally:
        if orig_api_key is not None:
            os.environ["API_KEY"] = orig_api_key

def test_review_idempotency_by_commit_id():
    """Verify is_review_submitted and publish_review do not re-submit reviews for same commit."""
    mock_client = MagicMock()
    mock_client.token = "token"
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.json.return_value = [
        {"id": 1, "commit_id": "sha-already-reviewed", "state": "COMMENTED"}
    ]
    mock_client.get.return_value = mock_resp

    # Should detect existing review for commit
    assert is_review_submitted(mock_client, "owner", "repo", 1, "sha-already-reviewed") is True
    # Should detect no review for new commit
    assert is_review_submitted(mock_client, "owner", "repo", 1, "sha-new-commit") is False

    # Calling publish_review for already reviewed commit should skip posting
    publish_review(mock_client, "owner", "repo", 1, "sha-already-reviewed", [{"body": "test"}])
    mock_client.session.post.assert_not_called()

def test_triage_idempotency_by_body_hash():
    """Verify body hash computation and duplicate triage check."""
    body1 = "This is a bug report about crashing on startup."
    body2 = "This is a bug report about crashing on startup. "  # extra whitespace stripped
    h1 = compute_body_hash(body1)
    h2 = compute_body_hash(body2)
    assert h1 == h2
    assert len(h1) == 64

    # Test checking GitHub comment for body hash
    mock_client = MagicMock()
    mock_client.token = "token"
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.json.return_value = [
        {"id": 100, "body": f"<!-- codesentinel:triage:body_hash={h1} -->\n**CodeSentinel AI Triage:**"}
    ]
    mock_client.get.return_value = mock_resp

    assert is_issue_already_triaged(99, h1, mock_client, "owner", "repo") is True
    assert is_issue_already_triaged(99, "different-body-hash", mock_client, "owner", "repo") is False

def test_fallback_model_on_429():
    """Verify fallback to fallback_model (openai/gpt-oss-120b) when primary model returns 429."""
    provider = OpenAICompatProvider(
        model="qwen/qwen3.8-27b",
        fallback_model="openai/gpt-oss-120b",
        api_key="test-key",
        base_url="https://api.groq.com/openai/v1"
    )

    resp_429 = MagicMock()
    resp_429.status_code = 429
    resp_429.ok = False
    resp_429.text = "Rate limit reached"

    resp_200 = MagicMock()
    resp_200.status_code = 200
    resp_200.ok = True
    resp_200.json.return_value = {
        "choices": [{"message": {"content": '{"message": "fallback response"}'}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
    }

    # First call returns 429, second call returns 200
    provider.session.post = MagicMock(side_effect=[resp_429, resp_200])

    result = provider.generate("system", "user", DummySchema)
    assert result.message == "fallback response"
    assert provider.session.post.call_count == 2
    
    # Second post payload model must be fallback model
    second_call_payload = provider.session.post.call_args_list[1][1]["json"]
    assert second_call_payload["model"] == "openai/gpt-oss-120b"

def test_token_and_cost_tracking():
    """Verify provider tracks accumulated token usage and dollar cost."""
    provider = OpenAICompatProvider(api_key="test-key")
    
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.ok = True
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": '{"message": "cost test"}'}}],
        "usage": {"prompt_tokens": 500, "completion_tokens": 200, "total_tokens": 700}
    }
    provider.session.post = MagicMock(return_value=mock_resp)

    provider.generate("sys", "usr", DummySchema)
    assert provider.total_tokens == 700
    assert provider.total_prompt_tokens == 500
    assert provider.total_completion_tokens == 200
    assert provider.total_cost_usd > 0.0

def test_retry_with_jitter_and_backoff():
    """Verify generate_with_retry applies backoff delay on failure."""
    calls = []
    
    def failing_func(sys, usr, schema):
        calls.append(time.time())
        if len(calls) < 2:
            raise ConnectionError("Temporary connection reset")
        return DummySchema(message="recovered")

    start = time.time()
    result = generate_with_retry(
        failing_func,
        "sys",
        "usr",
        DummySchema,
        max_retries=3,
        initial_delay=0.1,
        backoff_factor=2.0,
        jitter=True
    )
    elapsed = time.time() - start

    assert result.message == "recovered"
    assert len(calls) == 2
    # At least 0.1s delay due to backoff
    assert elapsed >= 0.1
