from codesentinel.github_client import GitHubClient

def publish_summary(client: GitHubClient, owner: str, repo: str, pr_number: int, summary: str, risk: str, checks: list, commit_id: str = ""):
    marker = "<!-- codesentinel:summary -->"
    body = f"{marker}\n<!-- codesentinel:last_sha={commit_id} -->\n## CodeSentinel AI Summary\n**Risk Level:** {risk.upper()}\n\n{summary}\n\n"
    if checks:
        body += "**Automated Checks:**\n"
        for check in checks:
            body += f"- :warning: {check}\n"

    # Find existing comment
    comments_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
    comments = client.get(comments_url).json()
    
    existing_id = None
    for c in comments:
        if marker in (c.get("body") or ""):
            existing_id = c["id"]
            break
            
    if existing_id:
        client.session.patch(f"https://api.github.com/repos/{owner}/{repo}/issues/comments/{existing_id}", json={"body": body})
    else:
        client.session.post(comments_url, json={"body": body})

def publish_review(client: GitHubClient, owner: str, repo: str, pr_number: int, commit_id: str, comments: list):
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
    payload = {
        "commit_id": commit_id,
        "event": "COMMENT",
        "comments": comments
    }
    client.session.post(url, json=payload).raise_for_status()
