import time
import os
from codesentinel.github_client import GitHubClient
from codesentinel.api.database import SessionLocal, IssueState, PRState
from codesentinel.triage.pipeline import run_triage_pipeline
from codesentinel.review.pipeline import run_pipeline

OWNER = 'kushmunjal'
REPO = 'codesentinel-test'
POLL_INTERVAL = 300 # 5 minutes

print(f'Starting CodeSentinel Daemon. Polling {OWNER}/{REPO} every 5 minutes...')

def run_daemon():
    client = GitHubClient()
    while True:
        print('Checking for new issues and PRs...')
        try:
            items = client.get_issues(OWNER, REPO)
            db = SessionLocal()
            
            for item in items:
                number = item['number']
                title = item['title']
                is_pr = 'pull_request' in item
                
                if is_pr:
                    # Check if PR exists in DB
                    db_pr = db.query(PRState).filter(PRState.number == number).first()
                    if not db_pr:
                        print(f'New PR detected: #{number}')
                        try:
                            # Add to DB first so we don't process it again if it crashes
                            new_pr = PRState(number=number, title=title, author=item.get('user', {}).get('login', 'unknown'), repo=REPO, status='In Review', risk_level='PENDING')
                            db.add(new_pr)
                            db.commit()
                            
                            run_pipeline(OWNER, REPO, number)
                            
                            # Update DB post-review (simplified)
                            new_pr.status = 'Reviewed'
                            db.commit()
                        except Exception as e:
                            print(f'Error processing PR #{number}: {e}')
                else:
                    # Check if Issue exists in DB
                    db_iss = db.query(IssueState).filter(IssueState.number == number).first()
                    if not db_iss:
                        print(f'New Issue detected: #{number}')
                        try:
                            # Add to DB first
                            new_iss = IssueState(number=number, title=title, status='Triaging', auto_type='pending', priority='Low')
                            db.add(new_iss)
                            db.commit()
                            
                            run_triage_pipeline(OWNER, REPO, number)
                            # (run_triage_pipeline now updates the DB itself)
                        except Exception as e:
                            print(f'Error processing Issue #{number}: {e}')
                            
            db.close()
        except Exception as e:
            print(f'Error fetching items from GitHub: {e}')
            
        print(f'Sleeping for {POLL_INTERVAL} seconds...')
        time.sleep(POLL_INTERVAL)

if __name__ == '__main__':
    run_daemon()
