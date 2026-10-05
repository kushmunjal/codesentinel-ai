from codesentinel.github_client import GitHubClient
from codesentinel.schemas import PRSummary

def publish_summary(client: GitHubClient, owner: str, repo: str, pr_number: int, summary_obj: PRSummary, context: dict, commit_id: str = ""):
    marker = "<!-- codesentinel:summary -->"
    body = f"{marker}\n<!-- codesentinel:last_sha={commit_id} -->\n## CodeSentinel AI Summary\n\n"
    
    # 1. Risk verdict with reasoning
    body += f"**Risk:** {summary_obj.risk_level.capitalize()} — {summary_obj.risk_reasoning}\n\n"
    
    # 9. Ready-to-merge explicit
    body += f"**Ready to Merge:** {context.get('ready_to_merge_text', 'No')}\n\n"

    # 2. Change overview grouped by intent
    if summary_obj.change_groups:
        body += "### 📝 Change Overview\n"
        for group in summary_obj.change_groups:
            body += f"- **{group.name}:** {group.description}\n"
        body += "\n"

    # 3. Findings breakdown
    findings_stats = context.get('findings_stats', {})
    if findings_stats:
        body += "### 🔍 Findings Breakdown\n"
        body += f"{findings_stats.get('counts_str', '0 issues')}\n\n"
        if findings_stats.get('top_concerns'):
            body += "**Top concerns:**\n"
            for concern in findings_stats['top_concerns']:
                body += f"- {concern}\n"
        body += "\n"

    # 5. Security-specific callout
    if context.get('has_security_findings'):
        body += "> [!CAUTION]\n> **SECURITY FINDINGS DETECTED** - Please review inline comments carefully.\n\n"

    # 4. Test coverage signal
    if context.get('tests_missing'):
        body += "> [!WARNING]\n> **Test Coverage:** Source logic changed with ZERO matching test changes.\n\n"
    else:
        body += "> [!NOTE]\n> **Test Coverage:** Satisfactory.\n\n"

    # 6. Breaking-change signal
    if summary_obj.breaking_change_suspected:
        body += f"> [!WARNING]\n> **Possible Breaking Change:** {summary_obj.breaking_change_reasoning or 'Please confirm public API/config changes.'}\n\n"

    # 7. Dependency changes
    if context.get('dependency_changes'):
        body += "### 📦 Dependency Changes\n"
        for dep in context['dependency_changes']:
            body += f"- {dep}\n"
        body += "\n"

    # 10. Guideline compliance
    if summary_obj.guideline_violations:
        body += "### 📏 Guideline Violations\n"
        for v in summary_obj.guideline_violations:
            body += f"- {v}\n"
        body += "\n"

    # 8. Review effort estimate
    body += f"**Review Effort:** {summary_obj.review_effort}/5 — {summary_obj.review_effort_reasoning}\n\n"

    # 11. Suggested reviewers
    if context.get('suggested_reviewers'):
        body += f"**Suggested Reviewers:** {', '.join(['@' + r for r in context['suggested_reviewers']])}\n\n"

    # 12. Linked context
    if context.get('linked_issues'):
        body += "### 🔗 Linked Context\n"
        for issue_info in context['linked_issues']:
            body += f"- Resolves #{issue_info['number']}: {issue_info['title']}\n"
        body += "\n"

    # 13. Footer
    body += f"---\n*View full details on the [CodeSentinel Console](http://127.0.0.1:8080).* \n"

    # Find existing comment
    comments_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
    comments = client.get(comments_url).json()
    
    existing_id = None
    for c in comments:
        if marker in (c.get("body") or ""):
            existing_id = c["id"]
            break
            
    if existing_id:
        client.session.patch(f"https://api.github.com/repos/{owner}/{repo}/issues/comments/{existing_id}", json={"body": body})
    else:
        client.session.post(comments_url, json={"body": body})

def publish_review(client: GitHubClient, owner: str, repo: str, pr_number: int, commit_id: str, comments: list):
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
    payload = {
        "commit_id": commit_id,
        "event": "COMMENT",
        "comments": comments
    }
    resp = client.session.post(url, json=payload)
    if not resp.ok:
        print("GITHUB ERROR:", resp.text)
    resp.raise_for_status()
