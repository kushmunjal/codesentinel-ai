with open("src/codesentinel/review/publish.py", "r") as f:
    content = f.read()

content = content.replace(
    'client.session.post(url, json=payload).raise_for_status()',
    'resp = client.session.post(url, json=payload)\n    if not resp.ok:\n        print("GITHUB ERROR:", resp.text)\n    resp.raise_for_status()'
)

with open("src/codesentinel/review/publish.py", "w") as f:
    f.write(content)
