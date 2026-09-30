import os
import sys

def main():
    event_name = os.environ.get("GITHUB_EVENT_NAME", "unknown")
    event_path = os.environ.get("GITHUB_EVENT_PATH", "")
    print(f"CodeSentinel AI invoked for event: {event_name}")
    print(f"Event payload path: {event_path}")
    sys.exit(0)

if __name__ == "__main__":
    main()
