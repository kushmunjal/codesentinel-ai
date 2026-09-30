def find_potential_duplicates(issue_title: str, issue_body: str, recent_issues: list[dict]) -> list[dict]:
    # Simple keyword heuristic
    words = set((issue_title + " " + (issue_body or "")).lower().split())
    duplicates = []
    
    for issue in recent_issues:
        target_words = set((issue.get("title", "") + " " + (issue.get("body", "") or "")).lower().split())
        overlap = len(words.intersection(target_words))
        if overlap >= 4:
            duplicates.append(issue)
            
    return duplicates
