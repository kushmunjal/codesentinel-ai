from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from codesentinel.api.database import engine, Base

app = FastAPI(title="CodeSentinel Console API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

# API Routes
@app.get("/api/stats")
def get_stats():
    return {
        "open_prs": 0,
        "ready_to_merge": 0,
        "needs_attention": 0,
        "open_issues": 0,
        "needs_triage": 0,
        "reviews_today": 0
    }

console_dist = os.path.join(os.path.expanduser("~"), "codesentinel-ai", "console", "dist")

@app.get("/", response_class=HTMLResponse)
@app.get("/{catchall:path}", response_class=HTMLResponse)
def serve_spa(catchall: str = ""):
    if catchall.startswith("api/"):
        return {"error": "Not Found"}
        
    index_file = os.path.join(console_dist, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r") as f:
            return f.read()
    return "Console not built yet."

if os.path.exists(console_dist):
    app.mount("/", StaticFiles(directory=console_dist), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8080)
