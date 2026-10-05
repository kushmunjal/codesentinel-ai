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

    if event_name == "pull_request":
        print(f"CodeSentinel AI invoked for {event_name} - PR #{pr_number}")
        run_pipeline(owner, repo, pr_number)
    elif event_name == "issue_comment":
        from codesentinel.commands import handle_comment
        print('Handling issue comment')
    elif event_name == "issues":
        print(f"CodeSentinel AI invoked for {event_name} - Issue #{issue_number}")
        run_triage_pipeline(owner, repo, issue_number)
    else:
        print(f"Event {event_name} not yet supported.")

if __name__ == "__main__":
    main()
