import hashlib
import json
import os
import time
from codesentinel.github_client import GitHubClient
from codesentinel.triage.duplicates import find_potential_duplicates
from codesentinel.llm.openai_compat import OpenAICompatProvider
from codesentinel.llm.retry import generate_with_retry
from codesentinel.schemas import TriageResult
from codesentinel.api.database import SessionLocal, IssueState
from codesentinel.review.context import parse_codeowners, resolve_reviewers, get_repo_config
from codesentinel.config import load_config
from codesentinel.observability.logger import get_logger
from codesentinel.observability.metrics import ISSUES_TRIAGED_TOTAL, LLM_LATENCY_SECONDS, LLM_REQUESTS_TOTAL


def compute_body_hash(body: str) -> str:
    return hashlib.sha256((body or "").encode("utf-8")).hexdigest()


def is_issue_already_triaged(client: GitHubClient, owner: str, repo: str, issue_number: int, body_hash: str) -> bool:
    try:
        comments_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments"
        resp = client.get(comments_url)
        if resp.status_code == 200:
            for comment in resp.json():
                body = comment.get("body", "")
                if f"<!-- codesentinel:triage:body_hash={body_hash} -->" in body:
                    return True
    except Exception:
        pass
    return False


def run_triage_pipeline(owner: str, repo: str, issue_number: int):
    run_id = f"triage-{owner}-{repo}-{issue_number}-{int(time.time())}"
    repo_name = f"{owner}/{repo}"
    logger = get_logger("triage", repo=repo_name, issue_number=issue_number, run_id=run_id)
    logger.info(f"Starting issue triage pipeline for {repo_name}#{issue_number}")

    client = GitHubClient()
    logger.info(f"Fetching issue details for {repo_name}#{issue_number}")
    print(f"Fetching issue {owner}/{repo}#{issue_number}")
    issue = client.get_issue(owner, repo, issue_number)
    
    body_hash = compute_body_hash(issue.get("body", ""))
    
    # Check DB and GitHub comment for idempotency
    db = SessionLocal()
    db_iss = db.query(IssueState).filter(IssueState.number == issue_number).first()
    if db_iss and db_iss.last_triaged_body_hash == body_hash and db_iss.status == "Triaged":
        logger.info(f"Issue #{issue_number} already triaged with body hash {body_hash}. Skipping.")
        print(f"Issue #{issue_number} already triaged with body hash {body_hash}. Skipping.")
        db.close()
        return

    if is_issue_already_triaged(client, owner, repo, issue_number, body_hash):
        logger.info(f"Idempotency: Issue #{issue_number} already contains triage comment for body hash {body_hash}. Skipping.")
        print(f"Idempotency: Issue #{issue_number} already contains triage comment for body hash {body_hash}. Skipping.")
        db.close()
        return
    db.close()

    try:
        print("Fetching repository labels...")
        labels = client.get_labels(owner, repo)
        label_names = [lbl["name"] for lbl in labels]
        
        print("Checking for duplicates...")
        recent_issues = client.get_issues(owner, repo)
        recent_issues = [i for i in recent_issues if i["number"] != issue_number]
        dupes = find_potential_duplicates(issue["title"], issue.get("body", ""), recent_issues)
        if dupes:
            logger.info("Potential duplicates detected", extra={"duplicates_count": len(dupes)})

        config = load_config()
        llm = OpenAICompatProvider(
            model=config.model,
            fallback_model=config.fallback_model,
            base_url=config.base_url,
            api_key=config.api_key
        )
        llm_model = config.model
        
        logger.info("Generating triage result with LLM", extra={"model": llm_model})
        print("Generating Triage Result...")
        user_prompt = f"Available Labels: {', '.join(label_names)}\n\nIssue Title: {issue['title']}\n\nIssue Body: {issue.get('body', '')}"
        if dupes:
            user_prompt += f"\n\nPotential duplicate detected: #{dupes[0]['number']} - {dupes[0]['title']}"
            
        prompt_path = os.path.join(os.environ.get("ACTION_PATH", os.path.join(os.path.dirname(__file__), "../../..")), "prompts/triage.md")
        with open(prompt_path) as f:
            triage_prompt = f.read()

        t0 = time.time()
        try:
            result = generate_with_retry(
                llm.generate,
                triage_prompt,
                user_prompt,
                TriageResult
            )
            elapsed = time.time() - t0
            LLM_LATENCY_SECONDS.labels(model=llm_model).observe(elapsed)
            LLM_REQUESTS_TOTAL.labels(model=llm_model, status="success").inc()
        except Exception:
            elapsed = time.time() - t0
            LLM_LATENCY_SECONDS.labels(model=llm_model).observe(elapsed)
            LLM_REQUESTS_TOTAL.labels(model=llm_model, status="error").inc()
            raise
            
        codeowners_content = client.get_file_content(owner, repo, "CODEOWNERS")
        if not codeowners_content:
            codeowners_content = client.get_file_content(owner, repo, ".github/CODEOWNERS")
            
        suggested_reviewers = []
        if codeowners_content:
            owners_map = parse_codeowners(codeowners_content)
            body_words = issue.get("body", "").split()
            potential_files = [w for w in body_words if "/" in w or w.endswith(".py") or w.endswith(".js")]
            suggested_reviewers = resolve_reviewers(potential_files, owners_map)
            
        readme = client.get_file_content(owner, repo, "README.md")
        related_docs = []
        if readme:
            issue_keywords = set(issue["title"].lower().split())
            for line in readme.splitlines():
                if any(k in line.lower() for k in issue_keywords if len(k) > 4):
                    related_docs.append(line.strip())
                    if len(related_docs) > 2: break

        repo_config = get_repo_config(client, owner, repo)
        verbosity = repo_config.get("verbosity", "detailed")

        comment_body = []
        comment_body.append(f"<!-- codesentinel:triage:body_hash={body_hash} -->")
        comment_body.append(f"**Classification:** {result.type}, {result.priority} priority ? {result.classification_reasoning}")
        
        if result.missing_info_specific:
            comment_body.append("### ?? Missing Information")
            for info in result.missing_info_specific:
                comment_body.append(f"- {info}")
                
        if result.duplicate_of:
            comment_body.append(f"### ?? Potential Duplicate of #{result.duplicate_of}")
            if result.duplicate_reasoning:
                comment_body.append(result.duplicate_reasoning)
                
        if result.suggested_reply:
            comment_body.append(f"\n{result.suggested_reply}\n")
                
        if suggested_reviewers and verbosity == "detailed":
            comment_body.append(f"**Suggested Assignees:** {', '.join(['@' + r for r in suggested_reviewers])}")
            
        if related_docs and verbosity == "detailed":
            comment_body.append("### ?? Related Documentation")
            for doc in related_docs:
                comment_body.append(f"- > {doc}")
                
        if result.missing_info_specific:
            comment_body.append("\n*We need a bit more info before this can be triaged ? see above.*")
        else:
            comment_body.append("\n*A maintainer will review this soon ? thanks for the detailed report!*")

        valid_labels = [lbl for lbl in result.labels if lbl in label_names][:3]
        logger.info("Applying issue labels", extra={"valid_labels": valid_labels})
        print(f"Applying labels: {valid_labels}")
        if valid_labels:
            client.add_labels_to_issue(owner, repo, issue_number, valid_labels)
            
        if comment_body:
            full_comment = "**CodeSentinel AI Triage:**\n\n" + "\n\n".join(comment_body)
            logger.info("Adding triage comment to issue")
            print("Adding triage comment...")
            client.add_comment_to_issue(owner, repo, issue_number, full_comment)
            
        issue_type = (result.type or "unknown").lower()
        issue_priority = (result.priority or "low").lower()
        ISSUES_TRIAGED_TOTAL.labels(
            repo=repo_name,
            type=issue_type,
            priority=issue_priority
        ).inc()

        db = SessionLocal()
        db_issue = db.query(IssueState).filter(IssueState.number == issue_number).first()
        if not db_issue:
            db_issue = IssueState(number=issue_number, title=issue["title"])
            db.add(db_issue)
     
        db_issue.auto_type = valid_labels[0] if valid_labels else 'unknown'
        db_issue.priority = result.priority.capitalize() if result.priority else 'Low'
        db_issue.status = 'Triaged'
        db_issue.last_triaged_body_hash = body_hash
     
        db.commit()
        db.close()
     
        os.makedirs("dashboard", exist_ok=True)
        with open("dashboard/latest_triage.json", "w") as f:
            json.dump({
                "title": issue["title"],
                "labels": valid_labels,
                "priority": result.priority,
                "comment": result.suggested_reply,
                "duplicate_flag": len(dupes) > 0
            }, f)
            
        logger.info("Issue triage pipeline completed successfully", extra={
            "type": issue_type,
            "priority": issue_priority,
            "labels": valid_labels
        })
        print("Triage pipeline complete.")
    except Exception as e:
        logger.exception(f"Issue triage pipeline failed: {e}")
        raise
