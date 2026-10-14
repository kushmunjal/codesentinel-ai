import os
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from threading import Lock

import uvicorn
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from codesentinel.api.auth import router as auth_router
from codesentinel.api.auth import seed_default_user
from codesentinel.api.database import (
    IssueState,
    PRState,
    get_db,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    seed_default_user()
    yield

app = FastAPI(title="CodeSentinel Console API", lifespan=lifespan)

# --- In-Memory Rate Limiter for /api/ routes ---

class InMemoryRateLimiter:
    """Thread-safe sliding window in-memory rate limiter using Python standard library."""
    def __init__(self, requests_per_minute: int = 120, window_seconds: float = 60.0):
        self.rpm = int(os.environ.get("RATE_LIMIT_PER_MINUTE", str(requests_per_minute)))
        self.window = window_seconds
        self.requests = defaultdict(list)
        self.lock = Lock()

    def is_rate_limited(self, client_id: str) -> bool:
        now = time.time()
        with self.lock:
            cutoff = now - self.window
            # Discard timestamps outside sliding window
            self.requests[client_id] = [t for t in self.requests[client_id] if t > cutoff]
            if len(self.requests[client_id]) >= self.rpm:
                return True
            self.requests[client_id].append(now)
            return False

    def reset(self):
        """Reset all rate limiter counters (useful for testing)."""
        with self.lock:
            self.requests.clear()

rate_limiter = InMemoryRateLimiter(requests_per_minute=120)


# --- CORS Lockdown ---

DEFAULT_ALLOWED_ORIGINS = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
env_origins = os.environ.get("ALLOWED_ORIGINS")
allowed_origins: list[str] = (
    [origin.strip() for origin in env_origins.split(",") if origin.strip()]
    if env_origins
    else DEFAULT_ALLOWED_ORIGINS
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "Accept", "X-Requested-With"],
)


# --- Security Headers & Rate Limiting Middleware ---

@app.middleware("http")
async def security_and_rate_limit_middleware(request: Request, call_next):
    # 1. Rate limiting on /api/ routes
    if request.url.path.startswith("/api/"):
        client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        if not client_ip:
            client_ip = request.client.host if request.client else "127.0.0.1"

        if rate_limiter.is_rate_limited(client_ip):
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "detail": "Rate limit exceeded. Please retry after some time."
                },
                headers={
                    "Retry-After": "60",
                    "X-Content-Type-Options": "nosniff",
                    "X-Frame-Options": "DENY",
                }
            )

    # 2. Process request
    response = await call_next(request)

    # 3. Standard security headers (nosniff, DENY, CSP, XSS, Referrer)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "connect-src 'self' http://localhost:* http://127.0.0.1:* ws://localhost:* ws://127.0.0.1:*; "
        "frame-ancestors 'none';"
    )
    return response


# --- Startup Event ---

# Startup handled via lifespan


# --- Include Auth Router ---

app.include_router(auth_router)


# --- Core API Routes ---

@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    open_prs = db.query(PRState).count()
    ready_to_merge = db.query(PRState).filter(PRState.status == "Ready to merge").count()
    needs_attention = db.query(PRState).filter(PRState.status == "Needs attention").count()
    open_issues = db.query(IssueState).count()
    needs_triage = db.query(IssueState).filter(IssueState.status == "Needs Triage").count()

    return {
        "open_prs": open_prs,
        "ready_to_merge": ready_to_merge,
        "needs_attention": needs_attention,
        "open_issues": open_issues,
        "needs_triage": needs_triage,
        "reviews_today": open_prs
    }


@app.get("/api/prs")
def get_prs(db: Session = Depends(get_db)):
    prs = db.query(PRState).order_by(PRState.number.desc()).all()
    return [
        {
            "number": pr.number,
            "title": pr.title,
            "author": pr.author,
            "status": pr.status,
            "risk_level": pr.risk_level,
            "repo": pr.repo
        }
        for pr in prs
    ]


@app.get("/api/issues")
def get_issues(db: Session = Depends(get_db)):
    issues = db.query(IssueState).order_by(IssueState.number.desc()).all()
    return [
        {
            "number": iss.number,
            "title": iss.title,
            "status": iss.status,
            "auto_type": iss.auto_type,
            "priority": iss.priority
        }
        for iss in issues
    ]


# --- SPA Static File Serving ---

console_dist = os.path.join(os.path.expanduser("~"), "codesentinel-ai", "console", "dist")

if os.path.exists(os.path.join(console_dist, "assets")):
    app.mount("/assets", StaticFiles(directory=os.path.join(console_dist, "assets")), name="assets")


@app.get("/", response_class=HTMLResponse)
@app.get("/{catchall:path}", response_class=HTMLResponse)
def serve_spa(catchall: str = ""):
    if catchall.startswith("api/"):
        return JSONResponse({"error": "Not Found"}, status_code=404)

    file_path = os.path.join(console_dist, catchall)
    if catchall and os.path.isfile(file_path):
        return FileResponse(file_path)

    index_file = os.path.join(console_dist, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r") as f:
            return f.read()
    return "Console not built yet."


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8080)
