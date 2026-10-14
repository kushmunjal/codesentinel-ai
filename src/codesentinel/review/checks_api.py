from typing import List, Optional, Dict, Any
from codesentinel.github_client import GitHubClient
from codesentinel.schemas import Finding

SEVERITY_ANNOTATION_MAP = {
    "critical": "failure",
    "high": "failure",
    "medium": "warning",
    "low": "notice"
}

def create_check_run(
    client: GitHubClient,
    owner: str,
    repo: str,
    head_sha: str,
    name: str = "CodeSentinel Review",
    status: str = "completed",
    conclusion: Optional[str] = None,
    summary: str = "",
    text: str = "",
    annotations: Optional[List[Dict[str, Any]]] = None,
    findings: Optional[List[Finding]] = None,
    severity_threshold: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Creates a GitHub Check Run via GitHub Checks API.
    Handles findings conversion to annotations and conclusion derivation.
    """
    if not client or not client.token:
        print("Notice: No GitHub token available for Checks API.")
        return None

    # Derive annotations from findings if provided
    active_annotations = list(annotations or [])
    if findings:
        for f in findings:
            level = SEVERITY_ANNOTATION_MAP.get(f.severity.lower(), "notice")
            active_annotations.append({
                "path": f.file,
                "start_line": max(1, f.line),
                "end_line": max(1, f.line),
                "annotation_level": level,
                "message": f.explanation,
                "title": f"[{f.severity.upper()}] {f.category.capitalize()}"
            })

    # Derive conclusion if not explicitly set
    if conclusion is None:
        has_high_or_crit = any(
            (f.severity.lower() in ("critical", "high")) for f in (findings or [])
        ) or any(a.get("annotation_level") == "failure" for a in active_annotations)
        conclusion = "failure" if has_high_or_crit else "success"

    output_summary = summary or (f"Completed with {len(active_annotations)} findings." if active_annotations else "No issues found.")
    
    url = f"https://api.github.com/repos/{owner}/{repo}/check-runs"
    payload = {
        "name": name,
        "head_sha": head_sha,
        "status": status,
        "conclusion": conclusion,
        "output": {
            "title": name,
            "summary": output_summary,
            "text": text or "",
            "annotations": active_annotations[:50]  # GitHub Check Run limit
        }
    }

    try:
        resp = client.session.post(url, json=payload)
        if resp.status_code == 403:
            print("Notice: Insufficient permissions to create check run (token lacks checks:write).")
            return None
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"Warning: Failed to create check run: {e}")
        return None
