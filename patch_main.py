with open("src/codesentinel/main.py", "r") as f:
    content = f.read()

content = content.replace("elif event_name == \"issues\":", "elif event_name == \"issue_comment\":\n        from codesentinel.commands import handle_comment\n        print('Handling issue comment')\n    elif event_name == \"issues\":")
with open("src/codesentinel/main.py", "w") as f:
    f.write(content)
