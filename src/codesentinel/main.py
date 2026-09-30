import os
import sys
from codesentinel.review.pipeline import run_pipeline

def main():
    event_name = os.environ.get("GITHUB_EVENT_NAME", "pull_request")
    
    if event_name == "pull_request":
        # In a real action, we parse GITHUB_EVENT_PATH. For this script, we take env vars.
        owner = os.environ.get("TEST_OWNER", "kushmunjal")
        repo = os.environ.get("TEST_REPO", "codesentinel-test")
        pr_number = int(os.environ.get("TEST_PR", "1"))
        
        print(f"CodeSentinel AI invoked for {event_name}")
        run_pipeline(owner, repo, pr_number)
    else:
        print(f"Event {event_name} not yet supported.")

if __name__ == "__main__":
    main()
