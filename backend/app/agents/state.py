from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.core.limits import BudgetTracker, ResearchBudget, ResearchPolicy
from app.schemas.research import ResearchPlanSchema


class AgentState(BaseModel):
    run_id: str
    question: str
    objective: Optional[str] = None
    domain: str = "general"
    mode: str = "deep"
    
    current_stage: str = "intake"
    status: str = "INTAKE"
    
    policy: ResearchPolicy = Field(default_factory=ResearchPolicy)
    budget: ResearchBudget = Field(default_factory=ResearchBudget)
    budget_tracker: BudgetTracker = Field(default_factory=BudgetTracker)
    
    plan: Optional[ResearchPlanSchema] = None
    plan_approved: bool = False
    
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    claims: List[Dict[str, Any]] = Field(default_factory=list)
    contradictions: List[Dict[str, Any]] = Field(default_factory=list)
    analysis_results: Dict[str, Any] = Field(default_factory=dict)
    
    markdown_report: Optional[str] = None
    report_id: Optional[str] = None
    
    logs: List[str] = Field(default_factory=list)
    error_message: Optional[str] = None
