from codesentinel.github_client import GitHubClient

def fetch_pr_diff(owner: str, repo: str, pr_number: int, client: GitHubClient = None) -> str:
    if client is None:
        client = GitHubClient()
    return client.get_pr_diff(owner, repo, pr_number)
