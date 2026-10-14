from unittest.mock import MagicMock, patch

import pytest

from codesentinel.diff.fetch import fetch_pr_diff
from codesentinel.github_client import GitHubClient


def test_fetch_pr_diff_with_provided_client():
    mock_client = MagicMock(spec=GitHubClient)
    mock_client.get_pr_diff.return_value = "diff --git a/foo.py b/foo.py\n+x = 1"
    
    diff = fetch_pr_diff("octocat", "hello-world", 42, client=mock_client)
    
    mock_client.get_pr_diff.assert_called_once_with("octocat", "hello-world", 42)
    assert "foo.py" in diff
    assert "+x = 1" in diff

@patch("codesentinel.diff.fetch.GitHubClient")
def test_fetch_pr_diff_default_client(mock_client_cls):
    mock_instance = MagicMock()
    mock_instance.get_pr_diff.return_value = "diff --git a/bar.py b/bar.py\n+y = 2"
    mock_client_cls.return_value = mock_instance
    
    diff = fetch_pr_diff("octocat", "hello-world", 99)
    
    mock_client_cls.assert_called_once()
    mock_instance.get_pr_diff.assert_called_once_with("octocat", "hello-world", 99)
    assert "bar.py" in diff

def test_fetch_pr_diff_propagates_exception():
    mock_client = MagicMock(spec=GitHubClient)
    mock_client.get_pr_diff.side_effect = RuntimeError("API Rate Limit Exceeded")
    
    with pytest.raises(RuntimeError, match="API Rate Limit Exceeded"):
        fetch_pr_diff("octocat", "hello-world", 1, client=mock_client)
