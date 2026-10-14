import pytest
import os
import hmac
import hashlib
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException
from codesentinel.api.webhook import verify_webhook_signature, github_webhook
from codesentinel.api.main import app

def test_webhook_route_mounted():
    paths = []
    for route in app.routes:
        if hasattr(route, "path"):
            paths.append(route.path)
        elif hasattr(route, "original_router"):
            for sub in route.original_router.routes:
                paths.append(getattr(sub, "path", ""))
    assert "/api/webhook" in paths

def test_verify_webhook_signature():
    secret = "my-webhook-secret"
    body = b'{"zen": "Practicality beats purity."}'
    valid_sig = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    assert verify_webhook_signature(body, secret, valid_sig) is True
    assert verify_webhook_signature(body, secret, "sha256=invalid") is False
    assert verify_webhook_signature(body, secret, None) is False
    assert verify_webhook_signature(body, "wrong-secret", valid_sig) is False

@pytest.mark.anyio
async def test_webhook_ping_event():
    mock_req = MagicMock()
    mock_req.body = AsyncMock(return_value=b"{}")
    mock_req.json = AsyncMock(return_value={})

    res = await github_webhook(mock_req, x_hub_signature_256=None, x_github_event="ping")
    assert res["status"] == "ok"
    assert res["message"] == "pong"

@pytest.mark.anyio
async def test_webhook_pr_event():
    secret = "test-secret"
    body = b'{"action": "opened", "pull_request": {"number": 10}, "repository": {"full_name": "org/repo"}}'
    sig = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    mock_req = MagicMock()
    mock_req.body = AsyncMock(return_value=body)
    mock_req.json = AsyncMock(return_value={
        "action": "opened",
        "pull_request": {"number": 10},
        "repository": {"full_name": "org/repo"}
    })

    res = await github_webhook(mock_req, x_hub_signature_256=sig, x_github_event="pull_request")
    assert res["status"] == "received"
    assert res["pr_number"] == 10
    assert res["repo"] == "org/repo"

@pytest.mark.anyio
async def test_webhook_invalid_signature_raises_401():
    os.environ["WEBHOOK_SECRET"] = "super-secret"
    try:
        mock_req = MagicMock()
        mock_req.body = AsyncMock(return_value=b'{"action": "opened"}')
        mock_req.json = AsyncMock(return_value={"action": "opened"})

        with pytest.raises(HTTPException) as exc_info:
            await github_webhook(mock_req, x_hub_signature_256="sha256=bad", x_github_event="pull_request")
        assert exc_info.value.status_code == 401
    finally:
        del os.environ["WEBHOOK_SECRET"]
