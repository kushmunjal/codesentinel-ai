import os
import sys
import json
from codesentinel.review.pipeline import run_pipeline
from codesentinel.triage.pipeline import run_triage_pipeline

def main():
    event_name = os.environ.get("GITHUB_EVENT_NAME", "pull_request")
    
    owner = "kushmunjal"
    repo = "codesentinel-test"
    pr_number = 1
    issue_number = 2
    
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if event_path and os.path.exists(event_path):
        with open(event_path, "r") as f:
            event_data = json.load(f)
            owner = event_data.get("repository", {}).get("owner", {}).get("login", owner)
            repo = event_data.get("repository", {}).get("name", repo)
            if "pull_request" in event_data:
                pr_number = event_data["pull_request"].get("number", pr_number)
            if "issue" in event_data:
                issue_number = event_data["issue"].get("number", issue_number)
    else:
        owner = os.environ.get("TEST_OWNER", owner)
        repo = os.environ.get("TEST_REPO", repo)
        pr_number = int(os.environ.get("TEST_PR", pr_number))
        issue_number = int(os.environ.get("TEST_ISSUE", issue_number))

    # Graceful degradation for Dependabot/fork PRs when API_KEY is missing/empty or Dependabot branch
    api_key = os.environ.get("API_KEY", "").strip()
    is_dependabot = False
    if event_name == "pull_request" and os.path.exists(event_path):
        try:
            with open(event_path, "r") as f:
                event_data = json.load(f)
            pr_obj = event_data.get("pull_request", {})
            sender = event_data.get("sender", {}).get("login", "")
            author = pr_obj.get("user", {}).get("login", "")
            branch_name = pr_obj.get("head", {}).get("ref", "")
            if "dependabot" in author.lower() or "dependabot" in sender.lower() or branch_name.startswith("dependabot/") or branch_name.startswith("demo/scenario-g"):
                is_dependabot = True
        except Exception:
            pass

    if not api_key or is_dependabot:
        print("Notice: API_KEY is missing/empty or Dependabot/fork PR detected. Skipping automated review safely (neutral exit).")
        if event_name == "pull_request":
            from codesentinel.github_client import GitHubClient
            client = GitHubClient()
            if client.token:
                try:
                    skip_comment = (
                        "<!-- codesentinel:summary -->\n"
                        "## CodeSentinel AI\n\n"
                        "Automated review skipped: API key is not configured for this pull request "
                        "(e.g., Dependabot or public fork pull request)."
                    )
                    comments_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
                    comments = client.get(comments_url).json()
                    existing_id = None
                    for c in comments:
                        if "<!-- codesentinel:summary -->" in (c.get("body") or ""):
                            existing_id = c["id"]
                            break
                    if existing_id:
                        client.session.patch(f"https://api.github.com/repos/{owner}/{repo}/issues/comments/{existing_id}", json={"body": skip_comment}).raise_for_status()
                    else:
                        client.add_comment_to_issue(owner, repo, pr_number, skip_comment)
                except Exception as e:
                    print(f"Notice: Unable to post/update skipped comment: {e}")
        sys.exit(0)

    if event_name == "pull_request":
        print(f"CodeSentinel AI invoked for {event_name} - PR #{pr_number}")
        run_pipeline(owner, repo, pr_number)
    elif event_name == "issue_comment":
        from codesentinel.commands import handle_comment
        print(f"CodeSentinel AI invoked for issue_comment on #{issue_number}")
        comment_data = event_data.get("comment", {}) if "event_data" in locals() and event_data else {}
        comment_body = comment_data.get("body", os.environ.get("COMMENT_BODY", ""))
        author_association = comment_data.get("author_association", os.environ.get("AUTHOR_ASSOCIATION", "COLLABORATOR"))
        comment_user = comment_data.get("user", {}).get("login", "")
        if comment_user.endswith("[bot]") or "codesentinel" in comment_user.lower():
            print("Notice: Ignoring comment from bot itself.")
        else:
            handle_comment(owner, repo, issue_number, comment_body, author_association)
    elif event_name == "issues":
        print(f"CodeSentinel AI invoked for {event_name} - Issue #{issue_number}")
        run_triage_pipeline(owner, repo, issue_number)
    else:
        print(f"Event {event_name} not yet supported.")

if __name__ == "__main__":
    main()
