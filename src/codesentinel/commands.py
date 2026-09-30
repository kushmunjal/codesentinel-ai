import os
from codesentinel.github_client import GitHubClient
from codesentinel.review.pipeline import run_pipeline
from codesentinel.triage.pipeline import run_triage_pipeline

def handle_comment(owner: str, repo: str, issue_number: int, comment_body: str, author_association: str):
    if author_association not in ["OWNER", "MEMBER", "COLLABORATOR", "CONTRIBUTOR"]:
        print("Unauthorized user, ignoring command.")
        return
        
    cmd = comment_body.strip().lower()
    if cmd == "/sentinel review":
        run_pipeline(owner, repo, issue_number)
    elif cmd == "/sentinel triage":
        run_triage_pipeline(owner, repo, issue_number)
    elif cmd == "/sentinel ignore":
        print("Bot is ignoring this PR.")
