from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class SourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    run_id: str
    url: str
    canonical_url: Optional[str]
    title: str
    author: Optional[str]
    publication_date: Optional[str]
    source_type: str
    domain: Optional[str]
    relevance_score: float
    content_text: Optional[str]
    content_hash: Optional[str]
    metadata_json: Dict[str, Any]
    created_at: datetime


class EvidenceItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    run_id: str
    source_id: str
    claim_text: str
    supporting_text: str
    publication_date: Optional[str]
    retrieval_timestamp: datetime
    evidence_type: str
    confidence_score: float
    verification_status: str
    relationship: str
    created_at: datetime


class ClaimResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    run_id: str
    claim_text: str
    verification_status: str
    section_key: Optional[str]
    created_at: datetime


class ContradictionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    run_id: str
    topic: str
    claim_a: str
    claim_b: str
    source_a_id: Optional[str]
    source_b_id: Optional[str]
    description: str
    resolution_status: str
    created_at: datetime


class CoverageItem(BaseModel):
    subquestion_id: str
    question: str
    status: str
    evidence_count: int
    primary_source_count: int


class CoverageResponse(BaseModel):
    run_id: str
    overall_score: float
    items: List[CoverageItem]
