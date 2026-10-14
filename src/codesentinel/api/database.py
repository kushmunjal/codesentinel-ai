import os
import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, event
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

db_dir = os.path.join(os.path.expanduser("~"), "codesentinel-ai")
os.makedirs(db_dir, exist_ok=True)
db_path = os.environ.get("DATABASE_PATH", os.path.join(db_dir, "codesentinel.db"))

DATABASE_URL = f"sqlite:///{db_path}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False, "timeout": 15}
)

# Enable WAL mode, busy timeout, and foreign keys for SQLite
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class PRState(Base):
    __tablename__ = "prs"
    id = Column(Integer, primary_key=True, index=True)
    number = Column(Integer, unique=True, index=True)
    title = Column(String)
    author = Column(String)
    repo = Column(String)
    status = Column(String)  # Ready to merge, Needs attention, In Review, Skipped
    risk_level = Column(String)  # LOW, MEDIUM, HIGH, CRITICAL
    risk_reasoning = Column(Text, nullable=True)
    review_effort = Column(Integer, default=1)
    head_sha = Column(String, index=True, nullable=True)
    last_reviewed_sha = Column(String, nullable=True)
    findings_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    findings = relationship("FindingRecord", back_populates="pr", cascade="all, delete-orphan")

class FindingRecord(Base):
    __tablename__ = "findings"
    id = Column(Integer, primary_key=True, index=True)
    pr_id = Column(Integer, ForeignKey("prs.id", ondelete="CASCADE"), index=True, nullable=True)
    pr_number = Column(Integer, index=True)
    repo = Column(String, index=True)
    file = Column(String)
    line = Column(Integer)
    severity = Column(String, index=True)  # low, medium, high, critical
    category = Column(String, index=True)  # security, bug, performance, style
    explanation = Column(Text)
    suggested_fix = Column(Text, nullable=True)
    feedback = Column(String, nullable=True)  # useful, false_positive
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    pr = relationship("PRState", back_populates="findings")

class IssueState(Base):
    __tablename__ = "issues"
    id = Column(Integer, primary_key=True, index=True)
    number = Column(Integer, unique=True, index=True)
    title = Column(String)
    status = Column(String)  # Needs Triage, Triaged, Needs Info, Closed
    auto_type = Column(String)  # bug, enhancement, question, duplicate, unknown
    priority = Column(String)  # Low, Medium, High, Critical
    classification_reasoning = Column(Text, nullable=True)
    duplicate_of = Column(Integer, nullable=True)
    missing_info = Column(Text, nullable=True)  # JSON-encoded list
    last_triaged_body_hash = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class ActivityLog(Base):
    __tablename__ = "activity_log"
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String)
    repo = Column(String)
    target_id = Column(Integer)
    details = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="maintainer")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class CacheEntry(Base):
    __tablename__ = "cache_entries"
    chunk_hash = Column(String, primary_key=True, index=True)
    response_json = Column(Text)
    model = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class EvalMetricRecord(Base):
    __tablename__ = "eval_metrics"
    id = Column(Integer, primary_key=True, index=True)
    eval_name = Column(String)
    precision = Column(Float)
    recall = Column(Float)
    f1 = Column(Float)
    passed_count = Column(Integer)
    total_count = Column(Integer)
    details_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)
    import sqlite3
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(prs);")
    pr_cols = [c[1] for c in cur.fetchall()]
    for pr_col, col_type in [
        ("risk_reasoning", "TEXT"),
        ("review_effort", "INTEGER DEFAULT 1"),
        ("head_sha", "VARCHAR"),
        ("findings_count", "INTEGER DEFAULT 0")
    ]:
        if pr_col not in pr_cols:
            cur.execute(f"ALTER TABLE prs ADD COLUMN {pr_col} {col_type};")
            
    cur.execute("PRAGMA table_info(issues);")
    issue_cols = [c[1] for c in cur.fetchall()]
    for issue_col, col_type in [
        ("classification_reasoning", "TEXT"),
        ("duplicate_of", "INTEGER"),
        ("missing_info", "TEXT"),
        ("last_triaged_body_hash", "VARCHAR")
    ]:
        if issue_col not in issue_cols:
            cur.execute(f"ALTER TABLE issues ADD COLUMN {issue_col} {col_type};")
    conn.commit()
    conn.close()

init_db()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
