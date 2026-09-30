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

    def get_issue(self, owner: str, repo: str, issue_number: int) -> dict:
        url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"
        return self.get(url).json()

    def get_labels(self, owner: str, repo: str) -> list[dict]:
        url = f"https://api.github.com/repos/{owner}/{repo}/labels"
        return self.get(url).json()
        
    def get_issues(self, owner: str, repo: str, state="open", per_page=30) -> list[dict]:
        url = f"https://api.github.com/repos/{owner}/{repo}/issues?state={state}&per_page={per_page}"
        return self.get(url).json()

    def add_labels_to_issue(self, owner: str, repo: str, issue_number: int, labels: list[str]):
        url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/labels"
        self.session.post(url, json={"labels": labels}).raise_for_status()

    def add_comment_to_issue(self, owner: str, repo: str, issue_number: int, body: str):
        url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments"
        self.session.post(url, json={"body": body}).raise_for_status()
