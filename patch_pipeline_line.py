with open("src/codesentinel/review/pipeline.py", "r") as f:
    content = f.read()

import re
# Replace the gh_comments append logic to use 'line' instead of 'position'
content = re.sub(
    r'"position": pos,',
    '"line": f.line,\n                "side": "RIGHT",',
    content
)

with open("src/codesentinel/review/pipeline.py", "w") as f:
    f.write(content)
