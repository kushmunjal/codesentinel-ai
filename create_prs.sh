#!/bin/bash
set -e
export PATH=$HOME/.local/bin:$PATH
cd ~/codesentinel-ai/test-repo

create_branch() {
  local branch=$1
  git checkout main
  git checkout -b $branch
}

create_pr() {
  local title=$1
  local body=$2
  local is_draft=$3
  git add .
  git commit -m "$title"
  git push origin HEAD
  if [ "$is_draft" = "true" ]; then
    gh pr create --draft --title "$title" --body "$body" > /dev/null
  else
    gh pr create --title "$title" --body "$body" > /dev/null
  fi
  echo "Created PR for branch"
}

create_branch clean-feature
echo -e 'def add(a, b):\n    return a + b' > math_operations.py
echo -e 'from math_operations import add\ndef test_add():\n    assert add(2, 3) == 5' > test_math.py
create_pr "Add basic math operations" "A small feature with tests included." false

create_branch hardcoded-secret
echo 'API_KEY="AIzaSyAxxxxxxxxxxxxxxxxxxxxxxx_xxxxx"' > config.py
create_pr "Add config module" "Sets up some configuration constants." false

create_branch logic-bug
echo -e 'def is_positive(n):\n    return n < 0' > utils.py
create_pr "Add is_positive helper" "Helper function for numbers." false

create_branch missing-tests
echo -e 'def fetch_data():\n    pass' > api.py
create_pr "Add fetch_data API" "Adds new API logic." false

create_branch large-refactor
for i in {1..5}; do
  for j in {1..50}; do
    echo "print('Line $j in file $i')" >> "refactor_$i.py"
  done
done
create_pr "Refactor project structure" "Mechanical changes across multiple files." false

create_branch perf-issue
echo -e 'def process_items(items):\n    result = []\n    for item in items:\n        for other in items:\n            if item == other:\n                result.append(item)\n    return result' > process.py
create_pr "Add item processing logic" "Processes items." false

create_branch docs-only
echo -e '\nNew documentation section' >> README.md
create_pr "Update README" "Clarify project description." false

create_branch draft-wip
echo "WIP" > wip.txt
create_pr "WIP: Experimental feature" "Still working on this." true

echo "All PRs created."
