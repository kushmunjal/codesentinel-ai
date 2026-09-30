import re

IGNORE_PATTERNS = [
    re.compile(r".*lock.*"),
    re.compile(r"^dist/.*"),
    re.compile(r"^build/.*"),
    re.compile(r".*\.min\.js$"),
    re.compile(r".*\.pyc$"),
]

def should_ignore(filepath: str) -> bool:
    for pattern in IGNORE_PATTERNS:
        if pattern.match(filepath):
            return True
    return False

def filter_diff(raw_diff: str) -> str:
    # A simple unified diff parser that drops ignored files.
    lines = raw_diff.split("\n")
    filtered_lines = []
    current_file = None
    skip_current = False
    
    for line in lines:
        if line.startswith("diff --git "):
            parts = line.split(" b/")
            if len(parts) > 1:
                current_file = parts[1]
            elif len(line.split(" ")) >= 4:
                current_file = line.split(" ")[-1][2:]
                
            skip_current = should_ignore(current_file) if current_file else False
        
        if not skip_current:
            filtered_lines.append(line)
            
    return "\n".join(filtered_lines)
