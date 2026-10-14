import os
from codesentinel.github_client import GitHubClient
from codesentinel.review.pipeline import run_pipeline
from codesentinel.triage.pipeline import run_triage_pipeline

def handle_comment(owner: str, repo: str, issue_number: int, comment_body: str, author_association: str):
    allowed_roles = ["OWNER", "MEMBER", "COLLABORATOR", "CONTRIBUTOR"]
    if author_association and author_association.upper() not in allowed_roles:
        print("Notice: Unauthorized user role, ignoring comment.")
        return
        
    cmd = (comment_body or "").strip().lower()
    if cmd == "/sentinel review":
        print(f"Executing slash command: /sentinel review on {owner}/{repo}#{issue_number}")
        run_pipeline(owner, repo, issue_number, force=True)
    elif cmd == "/sentinel triage":
        print(f"Executing slash command: /sentinel triage on {owner}/{repo}#{issue_number}")
        run_triage_pipeline(owner, repo, issue_number)
    elif cmd == "/sentinel ignore":
        print("Bot is ignoring this item.")
    else:
        # Check if this is an issue reply providing clarifying info
        try:
            client = GitHubClient()
            issue_data = client.get_issue(owner, repo, issue_number)
            if "pull_request" not in issue_data:
                print(f"User replied on issue #{issue_number}. Triggering updated triage...")
                run_triage_pipeline(owner, repo, issue_number)
        except Exception as e:
            print(f"Notice: Failed to process comment as triage update: {e}")
