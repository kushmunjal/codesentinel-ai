import os
import requests

class GitHubClient:
    def __init__(self, token: str = None):
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.session = requests.Session()
        if self.token:
            self.session.headers.update({
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github.v3+json"
            })
            
    def get(self, url: str, **kwargs):
        resp = self.session.get(url, **kwargs)
        resp.raise_for_status()
        return resp
        
    def get_pr_diff(self, owner: str, repo: str, pr_number: int) -> str:
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
        headers = {"Accept": "application/vnd.github.v3.diff"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        resp = self.session.get(url, headers=headers)
        resp.raise_for_status()
        return resp.text
