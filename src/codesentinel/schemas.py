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

class ChangeGroup(BaseModel):
    name: str = Field(..., description="E.g., Core logic, Tests, Docs/config, Dependencies")
    description: str = Field(..., description="One-line plain-English description of the group's purpose")

class PRSummary(BaseModel):
    summary: str = Field(..., description="High-level summary of the pull request.")
    risk_level: str = Field(..., description="Overall risk level: Low, Medium, High.")
    risk_reasoning: str = Field(..., description="Reasoning for the risk verdict based on findings.")
    change_groups: List[ChangeGroup] = Field(default_factory=list, description="Change overview grouped by intent.")
    review_effort: int = Field(..., description="1-5 scale.")
    review_effort_reasoning: str = Field(..., description="One-line reason for effort score.")
    breaking_change_suspected: bool = Field(False, description="True if public API/config changed.")
    breaking_change_reasoning: Optional[str] = Field(None, description="What might be breaking.")
    guideline_violations: List[str] = Field(default_factory=list, description="List of violated guidelines.")

class TriageResult(BaseModel):
    type: str = Field(..., description="E.g., Bug, Enhancement, Question")
    priority: str = Field(..., description="Priority: low, medium, high, critical.")
    classification_reasoning: str = Field(..., description="One-line why for type and priority.")
    labels: List[str] = Field(default_factory=list, description="List of suggested labels.")
    duplicate_of: Optional[int] = Field(None)
    duplicate_reasoning: Optional[str] = Field(None, description="Why it looks like a duplicate.")
    missing_info_specific: List[str] = Field(default_factory=list, description="Specific missing details requested from the user.")
    suggested_reply: Optional[str] = Field(None, description="Draft reply based on triage.")
