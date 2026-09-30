with open("src/codesentinel/review/pipeline.py", "r") as f:
    content = f.read()

# Update publish_summary call to include commit_id
content = content.replace(
    'publish_summary(client, owner, repo, pr_number, summary.summary, summary.risk_level, checks)',
    'publish_summary(client, owner, repo, pr_number, summary.summary, summary.risk_level, checks, commit_id)'
)

# Update publish_summary definition
with open("src/codesentinel/review/publish.py", "r") as f:
    pub_content = f.read()

pub_content = pub_content.replace(
    'def publish_summary(client: GitHubClient, owner: str, repo: str, pr_number: int, summary: str, risk: str, checks: list):',
    'def publish_summary(client: GitHubClient, owner: str, repo: str, pr_number: int, summary: str, risk: str, checks: list, commit_id: str = ""):'
)
pub_content = pub_content.replace(
    'body = f"{marker}\\n## CodeSentinel AI Summary\\n**Risk Level:** {risk.upper()}\\n\\n{summary}\\n\\n"',
    'body = f"{marker}\\n<!-- codesentinel:last_sha={commit_id} -->\\n## CodeSentinel AI Summary\\n**Risk Level:** {risk.upper()}\\n\\n{summary}\\n\\n"'
)

with open("src/codesentinel/review/pipeline.py", "w") as f:
    f.write(content)
with open("src/codesentinel/review/publish.py", "w") as f:
    f.write(pub_content)
