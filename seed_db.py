import os
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from codesentinel.api.database import Base, PRState, IssueState

db_path = os.path.join(os.path.expanduser("~"), "codesentinel-ai", "codesentinel.db")
engine = create_engine(f"sqlite:///{db_path}")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Add PRs
prs_data = [
    (1, "Add divide method and update subtract", "HIGH/CRITICAL", "Needs attention"),
    (3, "Add basic math operations", "LOW", "Ready to merge"),
    (4, "Add config module", "HIGH/CRITICAL", "Needs attention"),
    (5, "Add is_positive helper", "HIGH/CRITICAL", "Needs attention"),
    (6, "Add fetch_data API", "LOW", "Ready to merge"),
    (7, "Refactor project structure", "LOW", "Ready to merge"),
    (8, "Add item processing logic", "LOW", "Ready to merge"),
    (9, "Update README", "LOW", "Ready to merge"),
    (10, "WIP: Experimental feature", "LOW", "Needs attention")
]

for number, title, risk, status in prs_data:
    pr = session.query(PRState).filter_by(number=number).first()
    if not pr:
        pr = PRState(number=number, title=title, author="student", repo="codesentinel-test")
        session.add(pr)
    pr.status = status
    pr.risk_level = risk

# Add Issues
issues_data = [
    (2, "Bug: The calculator divide method crashes", "bug"),
    (11, "well-formed-bug", "bug"),
    (12, "vague-report", "question"),
    (13, "clear-duplicate", "duplicate"),
    (14, "feature-request", "enhancement")
]

for number, title, auto_type in issues_data:
    iss = session.query(IssueState).filter_by(number=number).first()
    if not iss:
        iss = IssueState(number=number, title=title, status="Needs Triage")
        session.add(iss)
    iss.auto_type = auto_type
    iss.priority = "High" if auto_type == "bug" else "Low"

session.commit()
session.close()
print("Database seeded.")
