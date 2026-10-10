from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field


class ToolCallResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    run_id: str
    stage: str
    tool_name: str
    arguments_json: Dict[str, Any]
    status: str
    result_summary: Optional[str]
    error_message: Optional[str]
    duration_ms: int
    retry_count: int
    created_at: datetime


class CustomToolCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: str = Field(..., min_length=10)
    tool_schema: Dict[str, Any] = Field(default_factory=dict, alias="schema_json")
    enabled: bool = True
    timeout_seconds: int = Field(30, ge=1, le=300)


class CustomToolResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    name: str
    description: str
    tool_schema: Dict[str, Any] = Field(..., alias="schema_json")
    enabled: bool
    timeout_seconds: int
    created_at: datetime
