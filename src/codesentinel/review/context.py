import re
from codesentinel.github_client import GitHubClient

def parse_codeowners(content: str) -> dict:
    """Returns a list of tuples (pattern, owners)."""
    owners_map = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.split()
        if len(parts) >= 2:
            owners_map.append((parts[0], parts[1:]))
    return owners_map

def resolve_reviewers(files: list[str], codeowners: list) -> list[str]:
    # Very simplified matching
    reviewers = set()
    for f in files:
        for pattern, owners in codeowners:
            if pattern == '*' or pattern in f or (pattern.endswith('/') and f.startswith(pattern)):
                reviewers.update(owners)
    return list(reviewers)

def extract_linked_issues(body: str) -> list[int]:
    if not body: return []
    matches = re.findall(r'(?i)(?:fixes|resolves|closes)\s+#(\d+)', body)
    return [int(m) for m in matches]

def parse_dependency_changes(diff_text: str) -> list[str]:
    # Very rudimentary dependency parsing
    deps = []
    lines = diff_text.splitlines()
    current_file = None
    for line in lines:
        if line.startswith('+++ b/'):
            current_file = line[6:]
        elif current_file and any(f in current_file for f in ['package.json', 'requirements.txt', 'pyproject.toml', 'Cargo.toml']):
            if line.startswith('+') and not line.startswith('+++'):
                deps.append(f"Added in {current_file}: {line[1:].strip()}")
            elif line.startswith('-') and not line.startswith('---'):
                deps.append(f"Removed in {current_file}: {line[1:].strip()}")
    return deps

def analyze_test_coverage(files_changed: list[str]) -> bool:
    src_changed = any(f.endswith('.py') or f.endswith('.js') or f.endswith('.ts') for f in files_changed if 'test' not in f.lower())
    tests_changed = any('test' in f.lower() for f in files_changed)
    if src_changed and not tests_changed:
        return False # No tests added for source changes
    return True

def get_repo_config(client: GitHubClient, owner: str, repo: str) -> dict:
    import yaml
    content = client.get_file_content(owner, repo, '.codesentinel.yml')
    if content:
        try:
            return yaml.safe_load(content) or {}
        except Exception:
            pass
    return {}
