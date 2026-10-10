from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    run_id: str
    title: str
    executive_summary: str
    full_markdown: str
    methodology: Optional[str]
    metadata_json: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class SummarizeReportRequest(BaseModel):
    summary_type: str = Field("executive", description="'executive', 'key_findings', or 'section_by_section'")


class SummarizeReportResponse(BaseModel):
    summary_type: str
    summary_text: str
    caveats_preserved: List[str]


class CitationValidationResponse(BaseModel):
    report_id: str
    is_valid: bool
    total_citations: int
    resolved_citations: int
    unsupported_claims: List[str]
    missing_sources: List[str]
