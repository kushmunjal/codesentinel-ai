from collections import defaultdict
from contextlib import asynccontextmanager
import os
from threading import Lock
import time

from fastapi import Depends, FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import text
import uvicorn

from codesentinel.api.auth import router as auth_router, seed_default_user
from codesentinel.api.database import IssueState, PRState, engine, get_db
from codesentinel.api.webhook import router as webhook_router
from codesentinel.config import load_config
from codesentinel.observability.metrics import (
    get_metrics_payload,
    REVIEWS_TOTAL,
    LLM_REQUESTS_TOTAL,
    CACHE_HITS_TOTAL,
    CACHE_MISSES_TOTAL,
    LLM_TOKENS_TOTAL,
    LLM_LATENCY_SECONDS
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
            self.requests[client_id] = [t for t in self.requests[client_id] if t > cutoff]
            if len(self.requests[client_id]) >= self.rpm:
                return True
            self.requests[client_id].append(now)
            return False

    def reset(self):
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

    response = await call_next(request)
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

# Include Routers
app.include_router(auth_router)
app.include_router(webhook_router)

# --- Observability Endpoints ---

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/readyz")
def readyz(response: Response = None):
    db_status = "ok"
    model_status = "ok"
    is_ready = True

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        is_ready = False
        db_status = f"Database unavailable: {e}"

    try:
        cfg = load_config()
        if not cfg.model:
            is_ready = False
            model_status = "Model configuration is missing"
    except Exception as e:
        is_ready = False
        model_status = f"Configuration error: {e}"

    if not is_ready:
        if response is not None:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "not_ready",
            "database": db_status,
            "model_config": model_status
        }

    if response is not None:
        response.status_code = status.HTTP_200_OK
    return {
        "status": "ready",
        "database": "ok",
        "model_config": "ok"
    }

@app.get("/metrics")
def metrics():
    payload, content_type = get_metrics_payload()
    return Response(content=payload, media_type=content_type)

@app.get("/api/metrics/summary")
def get_metrics_summary(db: Session = Depends(get_db)):
    try:
        total_reviews = int(sum(sample.value for sample in REVIEWS_TOTAL.collect()[0].samples if sample.name.endswith("_total")))
    except Exception:
        total_reviews = db.query(PRState).count()

    try:
        req_samples = LLM_REQUESTS_TOTAL.collect()[0].samples
        total_reqs = sum(s.value for s in req_samples if s.name.endswith("_total"))
        err_reqs = sum(s.value for s in req_samples if s.name.endswith("_total") and s.labels.get("status") == "error")
        error_rate = round(err_reqs / total_reqs, 4) if total_reqs > 0 else 0.0
    except Exception:
        error_rate = 0.0

    try:
        hits = sum(s.value for s in CACHE_HITS_TOTAL.collect()[0].samples if s.name.endswith("_total"))
        misses = sum(s.value for s in CACHE_MISSES_TOTAL.collect()[0].samples if s.name.endswith("_total"))
        total_cache = hits + misses
        cache_hit_rate = round(hits / total_cache, 4) if total_cache > 0 else 0.0
    except Exception:
        cache_hit_rate = 0.0

    try:
        token_samples = LLM_TOKENS_TOTAL.collect()[0].samples
        prompt_tokens = int(sum(s.value for s in token_samples if s.name.endswith("_total") and s.labels.get("direction") == "prompt"))
        completion_tokens = int(sum(s.value for s in token_samples if s.name.endswith("_total") and s.labels.get("direction") == "completion"))
    except Exception:
        prompt_tokens = 0
        completion_tokens = 0

    try:
        lat_samples = LLM_LATENCY_SECONDS.collect()[0].samples
        count_sample = next((s.value for s in lat_samples if s.name.endswith("_count")), 0)
        sum_sample = next((s.value for s in lat_samples if s.name.endswith("_sum")), 0)
        avg_latency = round(sum_sample / count_sample, 3) if count_sample > 0 else 0.0
    except Exception:
        avg_latency = 0.0

    return {
        "reviews_count": total_reviews,
        "error_rate": error_rate,
        "cache_hit_rate": cache_hit_rate,
        "token_counts": {
            "prompt": prompt_tokens,
            "completion": completion_tokens,
            "total": prompt_tokens + completion_tokens
        },
        "avg_latency": avg_latency
    }

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
    return [{"number": pr.number, "title": pr.title, "author": pr.author, "status": pr.status, "risk_level": pr.risk_level, "repo": pr.repo} for pr in prs]

@app.get("/api/issues")
def get_issues(db: Session = Depends(get_db)):
    issues = db.query(IssueState).order_by(IssueState.number.desc()).all()
    return [{"number": iss.number, "title": iss.title, "status": iss.status, "auto_type": iss.auto_type, "priority": iss.priority} for iss in issues]

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
