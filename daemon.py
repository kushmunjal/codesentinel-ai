import time
import os
from codesentinel.github_client import GitHubClient
from codesentinel.api.database import SessionLocal, IssueState, PRState
from codesentinel.triage.pipeline import run_triage_pipeline
from codesentinel.review.pipeline import run_pipeline

OWNER = os.environ.get("TEST_OWNER", "kushmunjal")
REPO = os.environ.get("TEST_REPO", "codesentinel-test")
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "10"))

print(f"Starting CodeSentinel Daemon. Polling {OWNER}/{REPO} every {POLL_INTERVAL}s...")

def poll_once():
    client = GitHubClient()
    items = client.get_issues(OWNER, REPO)
    db = SessionLocal()
    try:
        for item in items:
            number = item["number"]
            title = item.get("title", "")
            is_pr = "pull_request" in item
            
            if is_pr:
                db_pr = db.query(PRState).filter(PRState.number == number).first()
                if not db_pr:
                    print(f"New PR detected: #{number}")
                    try:
                        run_pipeline(OWNER, REPO, number)
                    except Exception as e:
                        print(f"Error reviewing PR #{number}: {e}")
                else:
                    try:
                        resp = client.get(f"https://api.github.com/repos/{OWNER}/{REPO}/pulls/{number}")
                        if getattr(resp, "ok", False) or getattr(resp, "status_code", 0) == 200:
                            pr_data = resp.json()
                            current_sha = pr_data.get("head", {}).get("sha", "")
                            if current_sha and current_sha != db_pr.last_reviewed_sha:
                                print(f"New commit detected on PR #{number} ({current_sha[:8]}). Running review...")
                                run_pipeline(OWNER, REPO, number)
                    except Exception as e:
                        print(f"Error checking PR #{number} update: {e}")
            else:
                db_iss = db.query(IssueState).filter(IssueState.number == number).first()
                if not db_iss:
                    print(f"New Issue detected: #{number}")
                    try:
                        run_triage_pipeline(OWNER, REPO, number)
                    except Exception as e:
                        print(f"Error triaging Issue #{number}: {e}")
                else:
                    try:
                        run_triage_pipeline(OWNER, REPO, number)
                    except Exception:
                        pass
    finally:
        db.close()

def run_daemon():
    while True:
        try:
            poll_once()
        except Exception as e:
            print(f"Daemon poll error: {e}")
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    run_daemon()
