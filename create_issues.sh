#!/bin/bash
set -e
export PATH=$HOME/.local/bin:$PATH
cd ~/codesentinel-ai/test-repo

create_issue() {
  local title=$1
  local body=$2
  gh issue create --title "$title" --body "$body" > /dev/null
  echo "Created issue: $title"
}

create_issue "well-formed-bug" "### Description\nWhen I call the add function with negative numbers, it throws an error instead of calculating.\n\n### Repro Steps\n1. Import add\n2. Call add(-1, -2)\n\n### Expected\nReturns -3\n\n### Actual\nThrows ValueError\n\n### Environment\nPython 3.12"

create_issue "vague-report" "it's broken, please fix"

create_issue "clear-duplicate" "### Bug Description\nWhen I call the add function with negative numbers, it crashes rather than calculating the result.\n\n### Steps to reproduce\n1. Import the add function\n2. Call add(-1, -2)\n\n### Expected Result\nShould return -3\n\n### Actual Result\nThrows a ValueError\n\n### Env\nPython 3.12"

create_issue "feature-request" "It would be great to add a multiply function to math_operations.py so we can do basic multiplication."

echo "All Issues created."
