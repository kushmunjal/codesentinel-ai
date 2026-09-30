from codesentinel.triage.duplicates import find_potential_duplicates

def test_find_potential_duplicates():
    issue_title = "Bug in login"
    issue_body = "The login page crashes when I type my password."
    recent = [
        {"number": 1, "title": "Login page crash", "body": "It crashes when typing password."},
        {"number": 2, "title": "Update README", "body": "Just updating docs."}
    ]
    
    dupes = find_potential_duplicates(issue_title, issue_body, recent)
    assert len(dupes) == 1
    assert dupes[0]["number"] == 1
