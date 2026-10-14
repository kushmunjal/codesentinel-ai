import json
import re
import os
import time
from codesentinel.github_client import GitHubClient
from codesentinel.diff.fetch import fetch_pr_diff
from codesentinel.diff.filter import filter_diff
from codesentinel.diff.chunk import chunk_diff
from codesentinel.diff.positions import map_line_to_position
from codesentinel.checks.secrets import scan_for_secrets, redact_secrets
from codesentinel.checks.heuristics import check_heuristics
from codesentinel.llm.openai_compat import OpenAICompatProvider
from codesentinel.llm.retry import generate_with_retry
from codesentinel.llm.cache import compute_chunk_hash, get_cached_chunk, set_cached_chunk
from codesentinel.schemas import ReviewResult, PRSummary
from codesentinel.review.publish import publish_summary, publish_review, is_review_submitted
from codesentinel.review.sarif import generate_sarif, write_sarif_file
from codesentinel.review.checks_api import create_check_run
from codesentinel.review.context import (
    parse_codeowners, resolve_reviewers, extract_linked_issues,
    parse_dependency_changes, analyze_test_coverage, get_repo_config
)
from codesentinel.config import load_config
from codesentinel.api.database import SessionLocal, PRState, FindingRecord
from codesentinel.observability.logger import get_logger
from codesentinel.observability.metrics import (
    ACTIVE_REVIEWS_GAUGE,
    FINDINGS_TOTAL,
    LLM_LATENCY_SECONDS,
    LLM_REQUESTS_TOTAL,
    REVIEWS_TOTAL
)

def get_pr_files(diff_text: str) -> list:
    files = []
    for line in diff_text.splitlines():
        if line.startswith('+++ b/'):
            files.append(line[6:])
    return files

def run_pipeline(owner: str, repo: str, pr_number: int):
    run_id = f"review-{owner}-{repo}-{pr_number}-{int(time.time())}"
    repo_name = f"{owner}/{repo}"
    logger = get_logger("review", repo=repo_name, pr_number=pr_number, run_id=run_id)
    ACTIVE_REVIEWS_GAUGE.inc()
    
    try:
        config = load_config()
        client = GitHubClient(token=config.github_token)

        # 1. Dependabot & missing API_KEY graceful degradation
        if not config.api_key:
            logger.info("Notice: API_KEY is missing or empty. Skipping automated review for PR (neutral exit).")
            print("Notice: API_KEY is missing or empty. Skipping automated review for PR (neutral exit).")
            if client.token:
                try:
                    summary_marker = "<!-- codesentinel:summary -->"
                    skip_body = (
                        f"{summary_marker}\n"
                        "## CodeSentinel AI\n\n"
                        ":information_source: **Automated review skipped**: API key is not configured for this pull request runner "
                        "(common on forks or Dependabot PRs). CodeSentinel exited safely with code 0."
                    )
                    comments_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
                    client.session.post(comments_url, json={"body": skip_body})
                except Exception as e:
                    logger.warning(f"Could not post neutral skip comment: {e}")

            db = SessionLocal()
            pr_state = db.query(PRState).filter(PRState.number == pr_number).first()
            if pr_state:
                pr_state.status = "Skipped"
                pr_state.risk_level = "LOW"
                db.commit()
            db.close()
            return

        logger.info(f"Fetching diff for {owner}/{repo}#{pr_number}")
        print(f"Fetching diff for {owner}/{repo}#{pr_number}")
        raw_diff = fetch_pr_diff(owner, repo, pr_number, client)
        filtered_diff = filter_diff(raw_diff)

        # 2. Secret Redaction before LLM transmission
        filtered_diff = redact_secrets(filtered_diff, allowlist=config.secret_allowlist)

        print("Running checks...")
        checks = scan_for_secrets(filtered_diff, allowlist=config.secret_allowlist) + check_heuristics(filtered_diff)

        print("Chunking diff...")
        chunks = chunk_diff(filtered_diff, max_tokens=config.max_tokens_per_chunk)

        llm = OpenAICompatProvider(
            model=config.model,
            fallback_model=config.fallback_model,
            base_url=config.base_url,
            api_key=config.api_key
        )
        llm_model = config.model

        repo_config = get_repo_config(client, owner, repo)
        verbosity = repo_config.get("verbosity", config.verbosity)
        guidelines = repo_config.get("guidelines", config.guidelines)
        guidelines_text = "\nRepo Guidelines:\n" + "\n".join([f"- {g}" for g in guidelines]) if guidelines else ""

        print("Generating Inline Reviews...")
        prompt_path = os.path.join(os.environ.get("ACTION_PATH", os.path.join(os.path.dirname(__file__), "../../..")), "prompts/review.md")
        with open(prompt_path) as f:
            review_prompt = f.read()

        all_findings = []
        for i, chunk in enumerate(chunks):
            # 3. Check token and cost budgets
            if llm.total_tokens > config.token_budget or llm.total_cost_usd > config.cost_budget_usd:
                logger.warning(f"Budget exceeded (Tokens: {llm.total_tokens}/{config.token_budget}, Cost: ${llm.total_cost_usd:.4f}/${config.cost_budget_usd}). Halting further chunk reviews.")
                print(f"Budget exceeded: stopping review for chunk {i+1}/{len(chunks)}.")
                break

            # 4. Check Diff Chunk Cache
            chunk_hash = compute_chunk_hash(chunk, config.model)
            cached_result = get_cached_chunk(chunk_hash)
            if cached_result:
                print(f"Cache hit for chunk {i+1}/{len(chunks)}")
                try:
                    res = ReviewResult.model_validate_json(cached_result)
                    all_findings.extend(res.findings)
                    continue
                except Exception:
                    pass

            user_prompt = f"Code Diff Chunk {i+1}/{len(chunks)}:{guidelines_text}\n\n{chunk}"
            t0 = time.time()
            try:
                res = generate_with_retry(
                    llm.generate,
                    review_prompt,
                    user_prompt,
                    ReviewResult
                )
                elapsed = time.time() - t0
                LLM_LATENCY_SECONDS.labels(model=llm_model).observe(elapsed)
                LLM_REQUESTS_TOTAL.labels(model=llm_model, status="success").inc()
                set_cached_chunk(chunk_hash, res.model_dump_json(), config.model)
                all_findings.extend(res.findings)
            except Exception:
                elapsed = time.time() - t0
                LLM_LATENCY_SECONDS.labels(model=llm_model).observe(elapsed)
                LLM_REQUESTS_TOTAL.labels(model=llm_model, status="error").inc()
                raise

        # Record findings metrics
        for f in all_findings:
            FINDINGS_TOTAL.labels(
                repo=repo_name,
                severity=(f.severity or "low").lower(),
                category=(f.category or "bug").lower()
            ).inc()

        # 5. Fetch PR details
        pr_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
        pr_data = client.get(pr_url).json()
        commit_id = pr_data.get("head", {}).get("sha", "")

        # 6. Publish Inline Comments (Idempotent check)
        review_comments = []
        for finding in all_findings:
            pos = map_line_to_position(raw_diff, finding.line)
            if pos != -1:
                comment_text = f"**[{finding.severity.upper()}] {finding.category}**\n{finding.explanation}"
                if finding.suggested_fix:
                    comment_text += f"\n\nSuggested fix:\n```python\n{finding.suggested_fix}\n```"
                review_comments.append({
                    "path": finding.file,
                    "position": pos,
                    "body": comment_text
                })

        if review_comments:
            if is_review_submitted(client, owner, repo, pr_number, commit_id):
                logger.info(f"Idempotency: Review for commit {commit_id} already published. Skipping duplicate review comments.")
                print(f"Review for commit {commit_id} already submitted. Skipping duplicate review comments.")
            else:
                logger.info(f"Publishing {len(review_comments)} review comments for commit {commit_id}")
                publish_review(client, owner, repo, pr_number, commit_id, review_comments)

        print("Generating PR Summary...")
        summary_prompt_path = os.path.join(os.environ.get("ACTION_PATH", os.path.join(os.path.dirname(__file__), "../../..")), "prompts/summary.md")
        with open(summary_prompt_path) as f:
            summary_prompt = f.read()

        summary_user_prompt = f"PR Diff Summary Input:\nPR Title: {pr_data.get('title')}\nPR Body: {pr_data.get('body')}\n\nDiff:\n{filtered_diff[:3000]}"
        t0 = time.time()
        try:
            summary_obj = generate_with_retry(
                llm.generate,
                summary_prompt,
                summary_user_prompt,
                PRSummary
            )
            elapsed = time.time() - t0
            LLM_LATENCY_SECONDS.labels(model=llm_model).observe(elapsed)
            LLM_REQUESTS_TOTAL.labels(model=llm_model, status="success").inc()
        except Exception:
            elapsed = time.time() - t0
            LLM_LATENCY_SECONDS.labels(model=llm_model).observe(elapsed)
            LLM_REQUESTS_TOTAL.labels(model=llm_model, status="error").inc()
            raise

        # Context Resolution
        files_changed = get_pr_files(raw_diff)
        codeowners_content = client.get_file_content(owner, repo, "CODEOWNERS")
        if not codeowners_content:
            codeowners_content = client.get_file_content(owner, repo, ".github/CODEOWNERS")
        owners_map = parse_codeowners(codeowners_content) if codeowners_content else []
        suggested_reviewers = resolve_reviewers(files_changed, owners_map)

        linked_issue_numbers = extract_linked_issues(pr_data.get("body", ""))
        linked_issues = []
        for num in linked_issue_numbers:
            try:
                iss = client.get_issue(owner, repo, num)
                linked_issues.append({"number": num, "title": iss.get("title", "")})
            except Exception:
                pass

        dependency_changes = parse_dependency_changes(raw_diff)
        tests_missing = not analyze_test_coverage(files_changed)

        sev_counts = {}
        for f in all_findings:
            sev_counts[f.severity] = sev_counts.get(f.severity, 0) + 1
        counts_str = ", ".join([f"{count} {sev}" for sev, count in sev_counts.items()]) if sev_counts else "No issues detected"
        top_concerns = [f"[{f.severity.upper()}] {f.explanation[:80]}..." for f in all_findings if f.severity in ["high", "critical"]]

        findings_stats = {
            "counts_str": counts_str,
            "top_concerns": top_concerns
        }

        context = {
            "ready_to_merge_text": "Yes" if summary_obj.risk_level.lower() == "low" and not checks else "No ? Open high/critical findings or warnings.",
            "findings_stats": findings_stats,
            "has_security_findings": any(f.category == "security" for f in all_findings),
            "tests_missing": tests_missing,
            "dependency_changes": dependency_changes,
            "suggested_reviewers": suggested_reviewers if verbosity == "detailed" else [],
            "linked_issues": linked_issues if verbosity == "detailed" else []
        }

        publish_summary(client, owner, repo, pr_number, summary_obj, context, commit_id)

        # 7. Generate SARIF and GitHub Check Run
        sarif_obj = generate_sarif(all_findings, repo_name=repo_name, commit_sha=commit_id)
        write_sarif_file(sarif_obj, "dashboard/review.sarif")
        write_sarif_file(sarif_obj, "codesentinel.sarif")

        create_check_run(
            client=client,
            owner=owner,
            repo=repo,
            head_sha=commit_id,
            findings=all_findings,
            severity_threshold=config.severity_threshold
        )

        # Record PR review metrics
        final_risk = summary_obj.risk_level.upper()
        REVIEWS_TOTAL.labels(
            repo=repo_name,
            risk=final_risk,
            status="success"
        ).inc()

        # Database persistence
        db = SessionLocal()
        pr_state = db.query(PRState).filter(PRState.number == pr_number).first()
        if not pr_state:
            pr_state = PRState(
                number=pr_number,
                title=pr_data.get("title", f"PR #{pr_number}"),
                author=pr_data.get("user", {}).get("login", "unknown"),
                repo=repo,
                head_sha=commit_id
            )
            db.add(pr_state)

        pr_state.head_sha = commit_id
        pr_state.risk_level = summary_obj.risk_level.upper()
        pr_state.risk_reasoning = summary_obj.risk_reasoning
        pr_state.review_effort = summary_obj.review_effort
        pr_state.findings_count = len(all_findings)
        pr_state.status = "Ready to merge" if summary_obj.risk_level.lower() == "low" and not checks else "Needs attention"
        pr_state.last_reviewed_sha = commit_id

        # Insert findings
        db.query(FindingRecord).filter(FindingRecord.pr_number == pr_number).delete()
        for f in all_findings:
            finding_rec = FindingRecord(
                pr_id=pr_state.id,
                pr_number=pr_number,
                repo=repo,
                file=f.file,
                line=f.line,
                severity=f.severity.lower(),
                category=f.category.lower(),
                explanation=f.explanation,
                suggested_fix=f.suggested_fix
            )
            db.add(finding_rec)

        db.commit()
        db.close()

        # Dashboard json export
        os.makedirs("dashboard", exist_ok=True)
        with open("dashboard/latest_review.json", "w") as f:
            json.dump({
                "summary": summary_obj.model_dump(),
                "findings": [f.model_dump() for f in all_findings],
                "diff": raw_diff
            }, f)

        logger.info("PR review pipeline completed successfully", extra={
            "risk_level": summary_obj.risk_level,
            "findings_count": len(all_findings),
            "status": pr_state.status
        })
        print(f"Pipeline finished. Risk: {summary_obj.risk_level}")
    except Exception as e:
        logger.exception(f"PR review pipeline failed: {e}")
        REVIEWS_TOTAL.labels(repo=repo_name, risk="UNKNOWN", status="error").inc()
        raise
    finally:
        ACTIVE_REVIEWS_GAUGE.dec()
