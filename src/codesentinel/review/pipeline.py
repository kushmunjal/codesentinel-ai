import json
from codesentinel.github_client import GitHubClient
from codesentinel.diff.fetch import fetch_pr_diff
from codesentinel.diff.filter import filter_diff
from codesentinel.diff.chunk import chunk_diff
from codesentinel.diff.positions import map_line_to_position
from codesentinel.checks.secrets import scan_for_secrets
from codesentinel.checks.heuristics import check_heuristics
from codesentinel.llm.openai_compat import OpenAICompatProvider
from codesentinel.llm.retry import generate_with_retry
from codesentinel.schemas import ReviewResult, PRSummary
from codesentinel.review.publish import publish_summary, publish_review

SYSTEM_PROMPT = """You are an expert AI code reviewer. Review the provided PR diff.
Focus on logic bugs, security vulnerabilities, and bad practices. Be concise.
Provide inline comments for issues found. Do NOT comment on trivial formatting."""

def run_pipeline(owner: str, repo: str, pr_number: int):
    client = GitHubClient()
    
    print(f"Fetching diff for {owner}/{repo}#{pr_number}")
    raw_diff = fetch_pr_diff(owner, repo, pr_number, client)
    filtered_diff = filter_diff(raw_diff)
    
    print("Running checks...")
    checks = scan_for_secrets(filtered_diff) + check_heuristics(filtered_diff)
    
    print("Chunking diff...")
    chunks = chunk_diff(filtered_diff, max_tokens=2000)
    
    llm = OpenAICompatProvider()
    
    print("Generating PR Summary...")
    summary = generate_with_retry(
        llm.generate,
        SYSTEM_PROMPT,
        f"Generate a high-level summary for this entire diff:\n\n{filtered_diff}",
        PRSummary
    )
    
    print("Generating Inline Reviews...")
    all_findings = []
    for chunk in chunks:
        result = generate_with_retry(
            llm.generate,
            SYSTEM_PROMPT,
            f"Review this diff chunk and provide findings:\n\n{chunk}",
            ReviewResult
        )
        all_findings.extend(result.findings)
        
    print(f"Found {len(all_findings)} issues. Validating...")
    
    # Save output for dashboard
    with open("dashboard/latest_review.json", "w") as f:
        json.dump({
            "summary": summary.model_dump(),
            "findings": [f.model_dump() for f in all_findings],
            "diff": filtered_diff
        }, f)

    # Convert findings to GitHub format
    gh_comments = []
    for f in all_findings:
        # We need the commit ID for the PR. Fetch it.
        pr_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
        pr_data = client.get(pr_url).json()
        commit_id = pr_data["head"]["sha"]
        
        pos = map_line_to_position(raw_diff, f.line)
        if pos > 0:
            gh_comments.append({
                "path": f.file,
                "position": pos,
                "body": f"**[{f.severity.upper()}] {f.category}**\n{f.explanation}\n\nSuggested fix:\n```python\n{f.suggested_fix}\n```"
            })
            
    print("Publishing to GitHub...")
    publish_summary(client, owner, repo, pr_number, summary.summary, summary.risk_level, checks)
    if gh_comments:
        publish_review(client, owner, repo, pr_number, commit_id, gh_comments)
    print("Pipeline complete.")
