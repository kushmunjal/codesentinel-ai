import os

db_dir = os.path.join(os.path.expanduser("~"), "codesentinel-ai")
os.makedirs(db_dir, exist_ok=True)
db_path = os.path.join(db_dir, "codesentinel.db")

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
import datetime

DATABASE_URL = f"sqlite:///{db_path}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class PRState(Base):
    __tablename__ = "prs"
    id = Column(Integer, primary_key=True, index=True)
    number = Column(Integer, unique=True, index=True)
    title = Column(String)
    author = Column(String)
    repo = Column(String)
    status = Column(String)
    risk_level = Column(String)
    last_reviewed_sha = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class IssueState(Base):
    __tablename__ = "issues"
    id = Column(Integer, primary_key=True, index=True)
    number = Column(Integer, unique=True, index=True)
    title = Column(String)
    status = Column(String)
    auto_type = Column(String)
    priority = Column(String)
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

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
