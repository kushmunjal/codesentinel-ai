import re

# Minimal secret regex (e.g., aws keys, standard bearer tokens)
SECRET_REGEXES = [
    re.compile(r"(?i)api[_-]?key[\s:=]+[\"'][a-zA-Z0-9_\-]{16,}[\"']"),
    re.compile(r"(?i)bearer\s+[a-zA-Z0-9_\-\.]+"),
    re.compile(r"AKIA[0-9A-Z]{16}")
]

def scan_for_secrets(diff_text: str) -> list[str]:
    secrets_found = []
    for line in diff_text.split("\n"):
        if line.startswith("+") and not line.startswith("+++"):
            for reg in SECRET_REGEXES:
                if reg.search(line):
                    secrets_found.append("Potential secret committed.")
                    break
    return secrets_found
