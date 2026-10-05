import json
import os
from codesentinel.github_client import GitHubClient
from codesentinel.triage.duplicates import find_potential_duplicates
from codesentinel.llm.openai_compat import OpenAICompatProvider
from codesentinel.llm.retry import generate_with_retry
from codesentinel.schemas import TriageResult
from codesentinel.api.database import SessionLocal, IssueState
from codesentinel.review.context import parse_codeowners, resolve_reviewers, get_repo_config

def run_triage_pipeline(owner: str, repo: str, issue_number: int):
    client = GitHubClient()
    
    print(f"Fetching issue {owner}/{repo}#{issue_number}")
    issue = client.get_issue(owner, repo, issue_number)
    
    print("Fetching repository labels...")
    labels = client.get_labels(owner, repo)
    label_names = [lbl["name"] for lbl in labels]
    
    print("Checking for duplicates...")
    recent_issues = client.get_issues(owner, repo)
    # Exclude current
    recent_issues = [i for i in recent_issues if i["number"] != issue_number]
    dupes = find_potential_duplicates(issue["title"], issue.get("body", ""), recent_issues)
    
    llm = OpenAICompatProvider()
    
    print("Generating Triage Result...")
    user_prompt = f"Available Labels: {', '.join(label_names)}\n\nIssue Title: {issue['title']}\n\nIssue Body: {issue.get('body', '')}"
    if dupes:
        user_prompt += f"\n\nPotential duplicate detected: #{dupes[0]['number']} - {dupes[0]['title']}"
        
    prompt_path = os.path.join(os.environ.get("ACTION_PATH", os.path.join(os.path.dirname(__file__), "../../..")), "prompts/triage.md")
    with open(prompt_path) as f:
        triage_prompt = f.read()

    result = generate_with_retry(
        llm.generate,
        triage_prompt,
        user_prompt,
        TriageResult
    )
    
    # Contextual resolving
    # Assignees via CODEOWNERS
    codeowners_content = client.get_file_content(owner, repo, "CODEOWNERS")
    if not codeowners_content:
        codeowners_content = client.get_file_content(owner, repo, ".github/CODEOWNERS")
        
    suggested_reviewers = []
    if codeowners_content:
        owners_map = parse_codeowners(codeowners_content)
        body_words = issue.get("body", "").split()
        potential_files = [w for w in body_words if "/" in w or w.endswith(".py") or w.endswith(".js")]
        suggested_reviewers = resolve_reviewers(potential_files, owners_map)
        
    # Related docs
    readme = client.get_file_content(owner, repo, "README.md")
    related_docs = []
    if readme:
        issue_keywords = set(issue["title"].lower().split())
        for line in readme.splitlines():
            if any(k in line.lower() for k in issue_keywords if len(k) > 4):
                related_docs.append(line.strip())
                if len(related_docs) > 2: break

    # Check verbosity
    repo_config = get_repo_config(client, owner, repo)
    verbosity = repo_config.get("verbosity", "detailed")

    # Format Triage Comment
    comment_body = []
    
    # 1. Classification
    comment_body.append(f"**Classification:** {result.type}, {result.priority} priority — {result.classification_reasoning}")
    
    # 2. Missing info
    if result.missing_info_specific:
        comment_body.append("### ⚠️ Missing Information")
        for info in result.missing_info_specific:
            comment_body.append(f"- {info}")
            
    # 3. Duplicate reasoning
    if result.duplicate_of:
        comment_body.append(f"### 🪞 Potential Duplicate of #{result.duplicate_of}")
        if result.duplicate_reasoning:
            comment_body.append(result.duplicate_reasoning)
            
    # Suggested Reply
    if result.suggested_reply:
        comment_body.append(f"\n{result.suggested_reply}\n")
            
    # 4. Suggested assignee
    if suggested_reviewers and verbosity == "detailed":
        comment_body.append(f"**Suggested Assignees:** {', '.join(['@' + r for r in suggested_reviewers])}")
        
    # 5. Related docs
    if related_docs and verbosity == "detailed":
        comment_body.append("### 📚 Related Documentation")
        for doc in related_docs:
            comment_body.append(f"- > {doc}")
            
    # 6. Footer
    if result.missing_info_specific:
        comment_body.append("\n*We need a bit more info before this can be triaged — see above.*")
    else:
        comment_body.append("\n*A maintainer will review this soon — thanks for the detailed report!*")

    # Filter only valid labels
    valid_labels = [lbl for lbl in result.labels if lbl in label_names][:3] # max 3
    print(f"Applying labels: {valid_labels}")
    if valid_labels:
        client.add_labels_to_issue(owner, repo, issue_number, valid_labels)
        
    if comment_body:
        full_comment = "**CodeSentinel AI Triage:**\n\n" + "\n\n".join(comment_body)
        print("Adding triage comment...")
        client.add_comment_to_issue(owner, repo, issue_number, full_comment)
        
    # Save output to database for dashboard
    db = SessionLocal()
    db_issue = db.query(IssueState).filter(IssueState.number == issue_number).first()
    if not db_issue:
        db_issue = IssueState(number=issue_number, title=issue["title"])
        db.add(db_issue)
 
    db_issue.auto_type = valid_labels[0] if valid_labels else 'unknown'
    db_issue.priority = result.priority.capitalize() if result.priority else 'Low'
    db_issue.status = 'Triaged'
 
    db.commit()
    db.close()
 
    # Save output for dashboard file
    os.makedirs("dashboard", exist_ok=True)
    with open("dashboard/latest_triage.json", "w") as f:
        json.dump({
            "title": issue["title"],
            "labels": valid_labels,
            "priority": result.priority,
            "comment": result.suggested_reply,
            "duplicate_flag": len(dupes) > 0
        }, f)
        
    print("Triage pipeline complete.")
