import json
from codesentinel.github_client import GitHubClient
from codesentinel.triage.duplicates import find_potential_duplicates
from codesentinel.llm.openai_compat import OpenAICompatProvider
from codesentinel.llm.retry import generate_with_retry
from codesentinel.schemas import TriageResult

SYSTEM_PROMPT = """You are an expert repository maintainer. 
Analyze the issue and assign the most appropriate labels from the allowed list. 
Also determine priority. If the issue is vague, write a comment asking for details."""

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
    
    dupe_comment = None
    if dupes:
        print("Found potential duplicates.")
        dupe_comment = f"CodeSentinel AI has detected this might be a duplicate of #{dupes[0]['number']}."
        
    llm = OpenAICompatProvider()
    
    print("Generating Triage Result...")
    user_prompt = f"Available Labels: {', '.join(label_names)}\n\nIssue Title: {issue['title']}\n\nIssue Body: {issue.get('body', '')}"
    
    result = generate_with_retry(
        llm.generate,
        SYSTEM_PROMPT,
        user_prompt,
        TriageResult
    )
    
    # Filter only valid labels
    valid_labels = [lbl for lbl in result.labels if lbl in label_names][:3] # max 3
    print(f"Applying labels: {valid_labels}")
    if valid_labels:
        client.add_labels_to_issue(owner, repo, issue_number, valid_labels)
        
    comment_body = []
    if result.comment:
        comment_body.append(result.comment)
    if dupe_comment:
        comment_body.append(dupe_comment)
        
    if comment_body:
        full_comment = "**CodeSentinel AI Triage:**\n" + "\n\n".join(comment_body)
        print("Adding triage comment...")
        client.add_comment_to_issue(owner, repo, issue_number, full_comment)
        
    # Save output for dashboard
    with open("dashboard/latest_triage.json", "w") as f:
        json.dump({
            "title": issue["title"],
            "labels": valid_labels,
            "priority": result.priority,
            "comment": result.comment,
            "duplicate_flag": len(dupes) > 0
        }, f)
        
    print("Triage pipeline complete.")
