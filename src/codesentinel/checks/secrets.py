import re
import math
from collections import Counter
from typing import List, Optional

# Specific secret patterns
SECRET_PATTERNS = [
    # AWS Access Key ID
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    # AWS Secret Access Key assignment
    re.compile(r"(?i)aws[_-]?secret[_-]?access[_-]?key[\s:=]+[\"']?([A-Za-z0-9/+=]{40})[\"']?"),
    # GitHub personal access / OAuth tokens
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{36,}\b"),
    # Google API Key
    re.compile(r"\bAIza[0-9A-Za-z\-_]{35}\b"),
    # Slack tokens (user, bot, app)
    re.compile(r"\bxox[baprs]-[0-9a-zA-Z\-]{10,72}\b"),
    # Generic bearer tokens
    re.compile(r"(?i)bearer\s+[a-zA-Z0-9_\-\.]{20,}"),
    # Generic API key assignments
    re.compile(r"(?i)(api[_-]?key|apikey|secret[_-]?key|auth[_-]?token)[\s:=]+[\"']([a-zA-Z0-9_\-]{16,})[\"']"),
    # Private keys (PEM)
    re.compile(r"-----BEGIN (?:[A-Z ]+)?PRIVATE KEY-----"),
]

# Multiline private key block
PRIVATE_KEY_BLOCK_REGEX = re.compile(
    r"-----BEGIN (?:[A-Z ]+)?PRIVATE KEY-----[\s\S]*?-----END (?:[A-Z ]+)?PRIVATE KEY-----"
)

# Candidate tokens for Shannon entropy check
CANDIDATE_TOKEN_REGEX = re.compile(r"[A-Za-z0-9+/=_\-]{17,}")

def shannon_entropy(data: str) -> float:
    """Calculates Shannon entropy of a string."""
    if not data:
        return 0.0
    entropy = 0.0
    length = len(data)
    counts = Counter(data)
    for count in counts.values():
        p = count / length
        entropy -= p * math.log2(p)
    return entropy

def _get_allowlist(allowlist: Optional[List[str]] = None) -> List[str]:
    if allowlist is not None:
        return allowlist
    try:
        from codesentinel.config import load_config
        return load_config().secret_allowlist or []
    except Exception:
        return []

def is_allowlisted(token: str, allowlist: List[str]) -> bool:
    """Checks whether a token or secret is matched by any pattern in the allowlist."""
    if not allowlist:
        return False
    for item in allowlist:
        if item == token or item in token:
            return True
        try:
            if re.search(item, token):
                return True
        except re.error:
            pass
    return False

def scan_for_secrets(diff_text: str, allowlist: Optional[List[str]] = None) -> List[str]:
    """
    Scans added lines in diff for known secret patterns and high Shannon entropy (> 4.5 on strings > 16 chars).
    Ignores secrets matching config.secret_allowlist.
    """
    active_allowlist = _get_allowlist(allowlist)
    secrets_found = []

    for line in diff_text.split("\n"):
        if not (line.startswith("+") and not line.startswith("+++")):
            continue
        content = line[1:].strip()

        # Check known regex patterns
        matched_regex = False
        for reg in SECRET_PATTERNS:
            match = reg.search(content)
            if match:
                matched_val = match.group(0)
                if not is_allowlisted(matched_val, active_allowlist):
                    secrets_found.append(f"Potential secret committed: matched {reg.pattern[:25]}...")
                    matched_regex = True
                    break
        if matched_regex:
            continue

        # Check Shannon entropy on candidate tokens > 16 chars
        candidates = CANDIDATE_TOKEN_REGEX.findall(content)
        for cand in candidates:
            if is_allowlisted(cand, active_allowlist):
                continue
            entropy = shannon_entropy(cand)
            if entropy > 4.5:
                secrets_found.append(f"Potential high-entropy secret committed (entropy={entropy:.2f} > 4.5).")
                break

    return secrets_found

def redact_secrets(diff_text: str, allowlist: Optional[List[str]] = None) -> str:
    """
    Replaces detected secrets/tokens with '[REDACTED_SECRET]' in diff text before LLM calls.
    Respects config.secret_allowlist.
    """
    active_allowlist = _get_allowlist(allowlist)
    
    # 1. First replace multiline private key blocks if any
    def _redact_private_key(match):
        block = match.group(0)
        if is_allowlisted(block, active_allowlist):
            return block
        return "[REDACTED_SECRET]"

    processed_text = PRIVATE_KEY_BLOCK_REGEX.sub(_redact_private_key, diff_text)

    # 2. Process line by line
    redacted_lines = []
    for line in processed_text.split("\n"):
        if not (line.startswith("+") and not line.startswith("+++")):
            redacted_lines.append(line)
            continue

        prefix = line[0]
        content = line[1:]

        # Known secret patterns redaction
        # AWS Key ID
        def _sub_aws(m):
            val = m.group(0)
            return val if is_allowlisted(val, active_allowlist) else "[REDACTED_SECRET]"
        content = re.sub(r"\bAKIA[0-9A-Z]{16}\b", _sub_aws, content)

        # GitHub token
        def _sub_gh(m):
            val = m.group(0)
            return val if is_allowlisted(val, active_allowlist) else "[REDACTED_SECRET]"
        content = re.sub(r"\bgh[pousr]_[A-Za-z0-9_]{36,}\b", _sub_gh, content)

        # Google API Key
        def _sub_google(m):
            val = m.group(0)
            return val if is_allowlisted(val, active_allowlist) else "[REDACTED_SECRET]"
        content = re.sub(r"\bAIza[0-9A-Za-z\-_]{35}\b", _sub_google, content)

        # Slack token
        def _sub_slack(m):
            val = m.group(0)
            return val if is_allowlisted(val, active_allowlist) else "[REDACTED_SECRET]"
        content = re.sub(r"\bxox[baprs]-[0-9a-zA-Z\-]{10,72}\b", _sub_slack, content)

        # Generic API key assignments
        def _sub_generic_key(m):
            val = m.group(2)
            if is_allowlisted(val, active_allowlist):
                return m.group(0)
            return m.group(0).replace(val, "[REDACTED_SECRET]")
        content = re.sub(
            r"(?i)(api[_-]?key|apikey|secret[_-]?key|auth[_-]?token)[\s:=]+[\"']([a-zA-Z0-9_\-]{16,})[\"']",
            _sub_generic_key,
            content
        )

        # Bearer tokens
        def _sub_bearer(m):
            full = m.group(0)
            parts = full.split(None, 1)
            if len(parts) == 2 and not is_allowlisted(parts[1], active_allowlist):
                return f"{parts[0]} [REDACTED_SECRET]"
            return full
        content = re.sub(r"(?i)bearer\s+[a-zA-Z0-9_\-\.]{20,}", _sub_bearer, content)

        # High entropy tokens (> 4.5 on strings > 16 chars)
        candidates = CANDIDATE_TOKEN_REGEX.findall(content)
        for cand in candidates:
            if cand in ("[REDACTED_SECRET]", "REDACTED_SECRET"):
                continue
            if is_allowlisted(cand, active_allowlist):
                continue
            if shannon_entropy(cand) > 4.5:
                content = content.replace(cand, "[REDACTED_SECRET]")

        redacted_lines.append(prefix + content)

    return "\n".join(redacted_lines)
