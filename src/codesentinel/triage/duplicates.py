import re
from typing import List, Dict, Set

# Common English stopwords to ignore in duplicate detection
STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by",
    "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't",
    "down", "during", "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have",
    "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself",
    "him", "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into",
    "is", "isn't", "it", "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my",
    "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our",
    "ours", "ourselves", "out", "over", "own", "same", "shan't", "she", "she'd", "she'll", "she's",
    "should", "shouldn't", "so", "some", "such", "than", "that", "that's", "the", "their", "theirs",
    "them", "themselves", "then", "there", "there's", "these", "they", "they'd", "they'll", "they're",
    "they've", "this", "those", "through", "to", "too", "under", "until", "up", "very", "was", "wasn't",
    "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what", "what's", "when", "when's",
    "where", "where's", "which", "while", "who", "who's", "whom", "why", "why's", "with", "won't",
    "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours", "yourself",
    "yourselves", "just", "please", "thanks", "thank", "also", "therefor", "issue", "bug"
}

def stem(word: str) -> str:
    """Lightweight suffix-stripping stemmer (Ponytail-compliant, stdlib only)."""
    w = word.lower()
    for suffix in ("ingly", "edly", "ing", "ed", "es", "s"):
        if len(w) > len(suffix) + 2 and w.endswith(suffix):
            w = w[:-len(suffix)]
            break
    if len(w) > 3 and w.endswith("e"):
        w = w[:-1]
    return w

def tokenize(text: str) -> Set[str]:
    """Extracts normalized, non-stopword tokens from text."""
    if not text:
        return set()
    raw_words = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return {stem(w) for w in raw_words if w not in STOPWORDS and len(w) > 1}

def jaccard_similarity(tokens1: Set[str], tokens2: Set[str]) -> float:
    """Calculates Jaccard similarity coefficient between two token sets."""
    if not tokens1 or not tokens2:
        return 0.0
    intersection = tokens1.intersection(tokens2)
    union = tokens1.union(tokens2)
    return len(intersection) / len(union) if union else 0.0

def find_potential_duplicates(
    issue_title: str,
    issue_body: str,
    recent_issues: List[Dict],
    threshold: float = 0.65
) -> List[Dict]:
    """
    Finds potential duplicate issues using tokenized Jaccard similarity (ignoring stopwords).
    Matches with similarity >= threshold (default 0.65).
    """
    combined_text = f"{issue_title or ''} {issue_body or ''}"
    source_tokens = tokenize(combined_text)
    if not source_tokens:
        return []

    duplicates = []
    for issue in recent_issues:
        target_text = f"{issue.get('title', '')} {issue.get('body', '')}"
        target_tokens = tokenize(target_text)
        similarity = jaccard_similarity(source_tokens, target_tokens)
        if similarity >= threshold:
            # Attach score for diagnostics/sorting
            issue_with_score = dict(issue)
            issue_with_score["similarity_score"] = similarity
            duplicates.append(issue_with_score)

    duplicates.sort(key=lambda x: x.get("similarity_score", 0.0), reverse=True)
    return duplicates
