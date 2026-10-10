from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ResearchCreate(BaseModel):
    question: str = Field(..., min_length=5, description="Main research question")
    objective: Optional[str] = Field(None, description="Research goal or target user outcome")
    domain: Optional[str] = Field("general", description="Topic domain e.g. technology, healthcare, finance")
    mode: str = Field("standard", description="quick, standard, indepth, deep, academic")
    recency_months: int = Field(24, ge=1, le=120)
    file_ids: List[str] = Field(default_factory=list)
    budget_overrides: Optional[Dict[str, Any]] = None



class SubQuestionSchema(BaseModel):
    id: str
    title: Optional[str] = None
    question: str
    search_queries: List[str]
    evidence_required: str
    status: str = "PENDING"


class ResearchPlanSchema(BaseModel):
    main_question: str
    subquestions: List[SubQuestionSchema]
    relevant_source_types: List[str]
    analytical_approach: str
    verification_strategy: str
    completion_criteria: str


class ResearchRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: Optional[str]
    question: str
    objective: Optional[str]
    domain: str
    mode: str
    status: str
    current_stage: str
    policy_json: Optional[Dict[str, Any]]
    budget_json: Optional[Dict[str, Any]]
    usage_json: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class ResearchPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    run_id: str
    version: int
    status: str
    main_question: str
    subquestions_json: List[Dict[str, Any]]
    plan_data_json: Dict[str, Any]
    user_feedback: Optional[str]
    created_at: datetime


class PlanRegenerateRequest(BaseModel):
    user_feedback: str = Field(..., min_length=3, description="Feedback to guide plan regeneration")


class PlanEditRequest(BaseModel):
    main_question: Optional[str] = None
    subquestions: Optional[List[Dict[str, Any]]] = None
