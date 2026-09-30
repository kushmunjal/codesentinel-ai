import pytest
from pydantic import BaseModel
from unittest.mock import MagicMock, patch
from codesentinel.llm.openai_compat import OpenAICompatProvider
from codesentinel.llm.retry import generate_with_retry
from codesentinel.schemas import PRSummary

class DummySchema(BaseModel):
    message: str

@patch("codesentinel.llm.openai_compat.requests.Session.post")
def test_openai_compat_provider(mock_post):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": '{"message": "hello"}'}}]
    }
    mock_post.return_value = mock_resp
    
    provider = OpenAICompatProvider(api_key="test-key")
    result = provider.generate("sys", "user", DummySchema)
    
    assert result.message == "hello"
    mock_post.assert_called_once()
    
def test_retry_success_after_failure():
    call_count = 0
    def mock_generate(sys_p, usr_p, schema):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise ValueError("Temporary network issue")
        return PRSummary(summary="Fixed", risk_level="low")
        
    result = generate_with_retry(mock_generate, "sys", "user", PRSummary)
    assert result.summary == "Fixed"
    assert call_count == 2
