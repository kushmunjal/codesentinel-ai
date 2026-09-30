import os
import sys
from codesentinel.review.pipeline import run_pipeline
from codesentinel.triage.pipeline import run_triage_pipeline

def main():
    event_name = os.environ.get("GITHUB_EVENT_NAME", "pull_request")
    
    if event_name == "pull_request":
        owner = os.environ.get("TEST_OWNER", "kushmunjal")
        repo = os.environ.get("TEST_REPO", "codesentinel-test")
        pr_number = int(os.environ.get("TEST_PR", "1"))
        print(f"CodeSentinel AI invoked for {event_name}")
        run_pipeline(owner, repo, pr_number)
    elif event_name == "issue_comment":
        from codesentinel.commands import handle_comment
        print('Handling issue comment')
    elif event_name == "issues":
        owner = os.environ.get("TEST_OWNER", "kushmunjal")
        repo = os.environ.get("TEST_REPO", "codesentinel-test")
        issue_number = int(os.environ.get("TEST_ISSUE", "2"))
        print(f"CodeSentinel AI invoked for {event_name}")
        run_triage_pipeline(owner, repo, issue_number)
    else:
        print(f"Event {event_name} not yet supported.")

if __name__ == "__main__":
    main()
