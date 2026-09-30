from pydantic import BaseModel, Field
from typing import List, Optional

class Finding(BaseModel):
    file: str = Field(..., description="The path to the file.")
    line: int = Field(..., description="The line number where the issue occurs.")
    severity: str = Field(..., description="Severity: low, medium, high, critical.")
    category: str = Field(..., description="Category: security, performance, style, bug.")
    explanation: str = Field(..., description="Explanation of the finding.")
    suggested_fix: Optional[str] = Field(None, description="Suggested code fix if applicable.")

class ReviewResult(BaseModel):
    findings: List[Finding] = Field(default_factory=list, description="List of findings in the chunk.")

class PRSummary(BaseModel):
    summary: str = Field(..., description="High-level summary of the pull request.")
    risk_level: str = Field(..., description="Overall risk level: low, medium, high.")

class TriageResult(BaseModel):
    labels: List[str] = Field(default_factory=list, description="List of suggested labels.")
    priority: str = Field(..., description="Priority: low, medium, high, critical.")
    comment: Optional[str] = Field(None, description="Optional comment to post on the issue.")
