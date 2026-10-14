from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
import datetime

class HealthResponse(BaseModel):
    status: str = "ok"
    database: str = "connected"
    version: str = "0.2.0"
    model: str
    fallback_model: Optional[str] = None

class FindingResponse(BaseModel):
    id: int
    pr_number: int
    repo: str
    file: str
    line: int
    severity: str  # low, medium, high, critical
    category: str  # security, bug, performance, style
    explanation: str
    suggested_fix: Optional[str] = None
    feedback: Optional[str] = None  # useful, false_positive
    created_at: datetime.datetime

class PRResponse(BaseModel):
    number: int
    title: str
    author: str
    repo: str
    status: str
    risk_level: str
    review_effort: int = 1
    head_sha: Optional[str] = None
    findings_count: int = 0
    updated_at: Optional[datetime.datetime] = None

class PRDetailResponse(PRResponse):
    risk_reasoning: Optional[str] = None
    last_reviewed_sha: Optional[str] = None
    findings: List[FindingResponse] = Field(default_factory=list)

class IssueResponse(BaseModel):
    number: int
    title: str
    status: str
    auto_type: str
    priority: str
    duplicate_of: Optional[int] = None
    updated_at: Optional[datetime.datetime] = None

class IssueDetailResponse(IssueResponse):
    classification_reasoning: Optional[str] = None
    missing_info: Optional[List[str]] = None

class StatsResponse(BaseModel):
    open_prs: int
    ready_to_merge: int
    needs_attention: int
    open_issues: int
    needs_triage: int
    reviews_today: int
    avg_latency_seconds: float = 0.0
    findings_by_severity: Dict[str, int] = Field(default_factory=dict)
    findings_by_category: Dict[str, int] = Field(default_factory=dict)

class FindingFeedbackRequest(BaseModel):
    feedback: str  # "useful" or "false_positive"

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str = "maintainer"

class EvalMetricResponse(BaseModel):
    eval_name: str
    precision: float
    recall: float
    f1: float
    passed_count: int
    total_count: int
    details: Optional[Dict[str, Any]] = None
    created_at: datetime.datetime
