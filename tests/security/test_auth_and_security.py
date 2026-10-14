import asyncio
import json
from datetime import timedelta

import pytest

from codesentinel.api.auth import (
    create_access_token,
    decode_access_token,
    hash_password,
    seed_default_user,
    verify_password,
)
from codesentinel.api.database import SessionLocal, User
from codesentinel.api.main import app, rate_limiter

# --- Helper for ASGI requests without external dependencies ---

async def make_asgi_request(
    app,
    method: str = "GET",
    path: str = "/api/health",
    headers: dict | None = None,
    body: bytes = b"",
    client_ip: str = "127.0.0.1",
):
    headers_list = [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()]
    response_headers = {}
    response_body = []
    status_code = [200]

    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": method,
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": headers_list,
        "client": (client_ip, 12345),
        "server": ("127.0.0.1", 8080),
        "app": app,
    }

    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(message):
        if message["type"] == "http.response.start":
            status_code[0] = message["status"]
            for k, v in message["headers"]:
                response_headers[k.decode("latin1").lower()] = v.decode("latin1")
        elif message["type"] == "http.response.body":
            response_body.append(message.get("body", b""))

    await app(scope, receive, send)
    return status_code[0], response_headers, b"".join(response_body)


# --- PBKDF2 Password Hashing Tests ---

def test_pbkdf2_hashing_and_verification():
    raw_pass = "SecureMaintainerPass!2026"
    hashed = hash_password(raw_pass)

    assert hashed.startswith("pbkdf2:sha256:100000$")
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("WrongPassword", hashed) is False
    assert verify_password("", hashed) is False
    assert verify_password(raw_pass, "invalid$hash$structure") is False


# --- JWT Token Generation & Verification Tests ---

def test_jwt_generation_and_validation():
    payload = {"sub": "test_maintainer", "role": "maintainer"}
    token = create_access_token(payload, expires_delta=timedelta(minutes=15))

    assert isinstance(token, str)
    assert token.count(".") == 2

    decoded = decode_access_token(token)
    assert decoded["sub"] == "test_maintainer"
    assert decoded["role"] == "maintainer"
    assert "exp" in decoded
    assert "iat" in decoded


def test_jwt_expiration():
    payload = {"sub": "expired_user", "role": "maintainer"}
    token = create_access_token(payload, expires_delta=timedelta(minutes=-1))

    with pytest.raises(ValueError, match="JWT token has expired"):
        decode_access_token(token)


def test_jwt_tampering_detection():
    token = create_access_token({"sub": "admin", "role": "maintainer"})
    parts = token.split(".")
    tampered_token = f"{parts[0]}.eyJzdWIiOiJoYWNrZXIifQ.{parts[2]}"

    with pytest.raises(ValueError, match="JWT signature verification failed"):
        decode_access_token(tampered_token)


# --- Maintainer User Seeding Tests ---

def test_seed_default_user():
    db = SessionLocal()
    try:
        seed_default_user(db)
        admin = db.query(User).filter(User.username == "admin").first()
        assert admin is not None
        assert admin.role == "maintainer"
        assert verify_password("admin123", admin.hashed_password) is True
    finally:
        db.close()


# --- Endpoint Tests: POST /api/auth/login and /api/auth/me ---

def test_login_success_and_authenticated_me():
    # 1. Login with valid credentials
    login_payload = json.dumps({"username": "admin", "password": "admin123"}).encode()
    status, _headers, body = asyncio.run(make_asgi_request(
        app,
        method="POST",
        path="/api/auth/login",
        headers={"content-type": "application/json", "content-length": str(len(login_payload))},
        body=login_payload,
    ))
    assert status == 200
    data = json.loads(body.decode())
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["username"] == "admin"
    assert data["role"] == "maintainer"

    token = data["access_token"]

    # 2. Access /api/auth/me using Bearer token
    status, _headers, body = asyncio.run(make_asgi_request(
        app,
        method="GET",
        path="/api/auth/me",
        headers={"authorization": f"Bearer {token}"},
    ))
    assert status == 200
    user_info = json.loads(body.decode())
    assert user_info["username"] == "admin"
    assert user_info["role"] == "maintainer"


def test_login_invalid_credentials():
    login_payload = json.dumps({"username": "admin", "password": "incorrect_password"}).encode()
    status, _headers, body = asyncio.run(make_asgi_request(
        app,
        method="POST",
        path="/api/auth/login",
        headers={"content-type": "application/json", "content-length": str(len(login_payload))},
        body=login_payload,
    ))
    assert status == 401
    data = json.loads(body.decode())
    assert "detail" in data


def test_get_current_user_unauthorized():
    status, _headers, _body = asyncio.run(make_asgi_request(
        app,
        method="GET",
        path="/api/auth/me",
    ))
    assert status == 401


# --- Security Headers Tests ---

def test_security_headers_present_on_responses():
    status, headers, _body = asyncio.run(make_asgi_request(app, method="GET", path="/api/health"))
    assert status == 200
    assert headers.get("x-content-type-options") == "nosniff"
    assert headers.get("x-frame-options") == "DENY"
    assert headers.get("x-xss-protection") == "1; mode=block"
    assert headers.get("referrer-policy") == "strict-origin-when-cross-origin"
    csp = headers.get("content-security-policy", "")
    assert "default-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp


# --- CORS Lockdown Tests ---

def test_cors_lockdown_allowed_and_disallowed_origins():
    # 1. Allowed Origin
    headers_allowed = [
        (b"origin", b"http://localhost:5173"),
        (b"access-control-request-method", b"POST"),
    ]
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "OPTIONS",
        "path": "/api/auth/login",
        "raw_path": b"/api/auth/login",
        "query_string": b"",
        "headers": headers_allowed,
        "client": ("127.0.0.1", 12345),
        "server": ("127.0.0.1", 8080),
        "app": app,
    }
    resp_headers = {}

    async def send_fn(msg):
        if msg["type"] == "http.response.start":
            for k, v in msg["headers"]:
                resp_headers[k.decode("latin1").lower()] = v.decode("latin1")

    async def recv_fn():
        return {"type": "http.request", "body": b"", "more_body": False}

    asyncio.run(app(scope, recv_fn, send_fn))
    assert resp_headers.get("access-control-allow-origin") == "http://localhost:5173"

    # 2. Disallowed Origin
    scope["headers"] = [
        (b"origin", b"https://malicious-site.attacker.com"),
        (b"access-control-request-method", b"POST"),
    ]
    resp_headers_evil = {}

    async def send_fn_evil(msg):
        if msg["type"] == "http.response.start":
            for k, v in msg["headers"]:
                resp_headers_evil[k.decode("latin1").lower()] = v.decode("latin1")

    asyncio.run(app(scope, recv_fn, send_fn_evil))
    assert resp_headers_evil.get("access-control-allow-origin") is None


# --- In-Memory Rate Limiting Tests ---

def test_rate_limiting_enforcement():
    rate_limiter.reset()
    rate_limiter.rpm = 3
    client_ip = "192.0.2.42"

    statuses = []
    for _ in range(5):
        st, _hdrs, _b = asyncio.run(make_asgi_request(
            app,
            method="GET",
            path="/api/health",
            client_ip=client_ip,
        ))
        statuses.append(st)

    # First 3 succeed, remaining are blocked with HTTP 429
    assert statuses == [200, 200, 200, 429, 429]
    rate_limiter.reset()
