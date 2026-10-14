import os
import hmac
import hashlib
from typing import Optional
from fastapi import APIRouter, Request, Header, HTTPException, status

router = APIRouter()

def verify_webhook_signature(payload_body: bytes, secret: str, signature_header: Optional[str]) -> bool:
    """Verifies GitHub HMAC-SHA256 signature from X-Hub-Signature-256 header."""
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    received_sig = signature_header[len("sha256="):]
    mac = hmac.new(secret.encode("utf-8"), msg=payload_body, digestmod=hashlib.sha256)
    expected_sig = mac.hexdigest()
    return hmac.compare_digest(expected_sig, received_sig)

@router.post("/api/webhook")
async def github_webhook(
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
    x_github_event: Optional[str] = Header("ping", alias="X-GitHub-Event")
):
    """
    Receives and processes GitHub webhook events with HMAC-SHA256 verification.
    """
    body_bytes = await request.body()
    secret = os.environ.get("WEBHOOK_SECRET")

    # If a webhook secret is configured, enforce verification
    if secret:
        if not verify_webhook_signature(body_bytes, secret, x_hub_signature_256):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing X-Hub-Signature-256"
            )

    try:
        payload = await request.json()
    except Exception:
        payload = {}

    if x_github_event == "ping":
        return {"status": "ok", "message": "pong"}

    if x_github_event == "pull_request":
        action = payload.get("action")
        pr_data = payload.get("pull_request", {})
        repo_data = payload.get("repository", {})
        return {
            "status": "received",
            "event": "pull_request",
            "action": action,
            "pr_number": pr_data.get("number"),
            "repo": repo_data.get("full_name")
        }

    if x_github_event == "issues":
        action = payload.get("action")
        issue_data = payload.get("issue", {})
        repo_data = payload.get("repository", {})
        return {
            "status": "received",
            "event": "issues",
            "action": action,
            "issue_number": issue_data.get("number"),
            "repo": repo_data.get("full_name")
        }

    return {"status": "ignored", "event": x_github_event}
