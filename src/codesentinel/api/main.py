from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
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

from fastapi import Depends
from sqlalchemy.orm import Session
from codesentinel.api.database import get_db, PRState, IssueState, ActivityLog

# API Routes
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
        from fastapi.responses import JSONResponse
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
