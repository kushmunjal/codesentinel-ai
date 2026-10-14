import json
import os
from codesentinel.github_client import GitHubClient
from codesentinel.diff.fetch import fetch_pr_diff
from codesentinel.diff.filter import filter_diff
from codesentinel.diff.chunk import chunk_diff
from codesentinel.diff.positions import map_line_to_position
from codesentinel.checks.secrets import scan_for_secrets, redact_secrets
from codesentinel.checks.heuristics import check_heuristics
from codesentinel.llm.openai_compat import OpenAICompatProvider
from codesentinel.llm.retry import generate_with_retry
from codesentinel.llm.cache import get_cached_chunk, set_cached_chunk
from codesentinel.schemas import ReviewResult, PRSummary
from codesentinel.review.publish import publish_summary, publish_review
from codesentinel.review.sarif import write_sarif
from codesentinel.review.checks_api import create_check_run
from codesentinel.review.context import (
    parse_codeowners, resolve_reviewers, extract_linked_issues,
    parse_dependency_changes, analyze_test_coverage, get_repo_config
)

def get_pr_files(diff_text: str) -> list:
    files = []
    for line in diff_text.splitlines():
        if line.startswith('+++ b/'):
            files.append(line[6:])
    return files

def run_pipeline(owner: str, repo: str, pr_number: int):
    client = GitHubClient()
    
    # 1. Dependabot / fork check: Gracefully skip if API_KEY is missing or empty
    api_key = os.environ.get("API_KEY", "").strip()
    if not api_key:
        print("Notice: API_KEY is missing or empty. Skipping automated review for PR (neutral exit).")
        if client.token:
            try:
                skip_comment = (
                    "<!-- codesentinel:summary -->\n"
                    "## CodeSentinel AI\n\n"
                    "Automated review skipped: API key is not configured for this pull request "
                    "(e.g., Dependabot or public fork pull request)."
                )
                client.add_comment_to_issue(owner, repo, pr_number, skip_comment)
            except Exception as e:
                print(f"Notice: Unable to post skipped review comment: {e}")
        try:
            from codesentinel.api.database import SessionLocal, PRState
            db = SessionLocal()
            pr_rec = db.query(PRState).filter(PRState.number == pr_number).first()
            if not pr_rec:
                pr_rec = PRState(number=pr_number, repo=f"{owner}/{repo}", status="Skipped")
                db.add(pr_rec)
            else:
                pr_rec.status = "Skipped"
            db.commit()
            db.close()
        except Exception:
            pass
        return

    print(f"Fetching diff for {owner}/{repo}#{pr_number}")
    raw_diff = fetch_pr_diff(owner, repo, pr_number, client)
    filtered_diff = filter_diff(raw_diff)
    
    print("Running checks...")
    checks = scan_for_secrets(filtered_diff) + check_heuristics(filtered_diff)
    if checks:
        print(f"Checks flagged {len(checks)} warnings:", checks)
    
    # Redact secrets from diff before chunking and LLM calls
    filtered_diff = redact_secrets(filtered_diff)

    print("Chunking diff...")
    chunks = chunk_diff(filtered_diff, max_tokens=2000)
    
    from codesentinel.config import load_config
    try:
        config = load_config()
    except Exception:
        config = None

    token_budget = config.token_budget if config else 100000
    cost_budget_usd = config.cost_budget_usd if config else 1.00

    llm = OpenAICompatProvider()
    
    repo_config = get_repo_config(client, owner, repo)
    verbosity = repo_config.get("verbosity", "detailed")
    guidelines = repo_config.get("guidelines", [])
    guidelines_text = "\nRepo Guidelines:\n" + "\n".join([f"- {g}" for g in guidelines]) if guidelines else ""
    
    print("Generating Inline Reviews...")
    prompt_path = os.path.join(os.environ.get("ACTION_PATH", os.path.join(os.path.dirname(__file__), "../../..")), "prompts/review.md")
    with open(prompt_path) as f:
        review_prompt = f.read()

    all_findings = []
    budget_exceeded = False

    for chunk in chunks:
        # Check token and cost budgets
        if llm.total_tokens >= token_budget:
            print(f"Warning: Token budget of {token_budget} exceeded (consumed {llm.total_tokens}). Halting chunk review.")
            budget_exceeded = True
            break
        if llm.total_cost_usd >= cost_budget_usd:
            print(f"Warning: Cost budget of ${cost_budget_usd:.2f} exceeded (consumed ${llm.total_cost_usd:.4f}). Halting chunk review.")
            budget_exceeded = True
            break

        cached_response = get_cached_chunk(chunk, llm.model)
        if cached_response:
            result = ReviewResult.model_validate_json(cached_response)
        else:
            result = generate_with_retry(
                llm.generate,
                review_prompt,
                f"Review this diff chunk and provide findings:\n\n{chunk}{guidelines_text}",
                ReviewResult
            )
            set_cached_chunk(chunk, result.model_dump_json(), llm.model)

        all_findings.extend(result.findings)
        
    print(f"Found {len(all_findings)} issues. Validating...")

    print("Generating PR Summary...")
    prompt_path = os.path.join(os.environ.get("ACTION_PATH", os.path.join(os.path.dirname(__file__), "../../..")), "prompts/summary.md")
    with open(prompt_path) as f:
        summary_prompt = f.read()

    if not budget_exceeded and (llm.total_tokens < token_budget and llm.total_cost_usd < cost_budget_usd):
        summary = generate_with_retry(
            llm.generate,
            summary_prompt,
            f"Generate a high-level summary for this entire diff. Consider these findings: {len(all_findings)} found.\n\nDiff:\n{filtered_diff}{guidelines_text}",
            PRSummary
        )
    else:
        print(f"Warning: Review halted: Token or cost budget limit reached ({llm.total_tokens} tokens, ${llm.total_cost_usd:.4f}).")
        summary = PRSummary(
            summary="Review partially completed: Automated review halted due to configured token or cost budget limit.",
            risk_level="Medium" if all_findings else "Low",
            risk_reasoning="Budget cap reached before full review synthesis.",
            review_effort=3,
            review_effort_reasoning="Budget limit reached during review run."
        )
    
    # Save output for dashboard
    os.makedirs("dashboard", exist_ok=True)
    with open("dashboard/latest_review.json", "w") as f:
        json.dump({
            "summary": summary.model_dump(),
            "findings": [f.model_dump() for f in all_findings],
            "diff": filtered_diff
        }, f)

    # Write SARIF v2.1.0 output
    write_sarif(all_findings, "dashboard/review.sarif")
    write_sarif(all_findings, "codesentinel.sarif")

    if verbosity == "concise":
        summary.change_groups = []
        summary.guideline_violations = []

    # Contextual resolution
    files_changed = get_pr_files(filtered_diff)
    
    # 1. CODEOWNERS
    codeowners_content = client.get_file_content(owner, repo, "CODEOWNERS")
    if not codeowners_content:
        codeowners_content = client.get_file_content(owner, repo, ".github/CODEOWNERS")
    suggested_reviewers = []
    if codeowners_content:
        owners_map = parse_codeowners(codeowners_content)
        suggested_reviewers = resolve_reviewers(files_changed, owners_map)
        
    # 2. Dependency changes
    dependency_changes = parse_dependency_changes(filtered_diff)
    
    # 3. Linked issues
    pr_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    pr_data = client.get(pr_url).json()
    linked_issue_nums = extract_linked_issues(pr_data.get("body", ""))
    linked_issues = []
    for num in linked_issue_nums:
        try:
            iss_data = client.get_issue(owner, repo, num)
            linked_issues.append({"number": num, "title": iss_data.get("title", "")})
        except Exception:
            pass

    # 4. Test coverage signal
    tests_missing = not analyze_test_coverage(files_changed)

    # 5. Security callout
    has_security_findings = any(f.category.lower() == 'security' for f in all_findings)

    # 6. Findings stats
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    top_concerns = []
    for f in all_findings:
        sev = f.severity.lower()
        if sev in counts: counts[sev] += 1
        if sev in ['critical', 'high'] and len(top_concerns) < 3:
            top_concerns.append(f"[{sev.upper()}] {f.explanation} (in {f.file})")
            
    counts_str = ", ".join([f"{v} {k}" for k, v in counts.items() if v > 0])
    if not counts_str: counts_str = "No issues found."

    # 7. Ready to merge
    ready = True
    ready_reason = []
    if counts['critical'] > 0 or counts['high'] > 0:
        ready = False
        ready_reason.append("Open high/critical findings.")
    if tests_missing:
        ready = False
        ready_reason.append("Tests missing for source changes.")
    if pr_data.get("draft"):
        ready = False
        ready_reason.append("PR is a draft.")
        
    ready_to_merge_text = "Yes" if ready else f"No ? {', '.join(ready_reason)}"

    context = {
        "suggested_reviewers": suggested_reviewers,
        "dependency_changes": dependency_changes,
        "linked_issues": linked_issues,
        "tests_missing": tests_missing,
        "has_security_findings": has_security_findings,
        "findings_stats": {
            "counts_str": counts_str,
            "top_concerns": top_concerns
        },
        "ready_to_merge_text": ready_to_merge_text
    }

    # Convert findings to GitHub format
    gh_comments = []
    commit_id = pr_data["head"]["sha"]
    for f in all_findings:
        pos = map_line_to_position(raw_diff, f.line)
        if pos > 0:
            gh_comments.append({
                "path": f.file,
                "line": f.line,
                "side": "RIGHT",
                "body": f"**[{f.severity.upper()}] {f.category}**\n{f.explanation}\n\nSuggested fix:\n```python\n{f.suggested_fix}\n```"
            })
            
    print("Publishing to GitHub...")
    publish_summary(client, owner, repo, pr_number, summary, context, commit_id)
    if gh_comments:
        publish_review(client, owner, repo, pr_number, commit_id, gh_comments)

    # Post Check Run via Checks API
    create_check_run(
        client,
        owner,
        repo,
        commit_id,
        name="CodeSentinel Review",
        findings=all_findings,
        summary=summary.summary
    )
    print("Pipeline complete.")

def check_limits(files_count, total_tokens):
    if files_count > 50 or total_tokens > 50000:
        raise ValueError("PR exceeds safe limits for automated review.")
