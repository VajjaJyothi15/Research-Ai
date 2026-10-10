from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel

from app.tools.web_search import WebSearchInput, execute_web_search
from app.tools.url_fetcher import FetchUrlInput, execute_fetch_url
from app.tools.academic_search import AcademicSearchInput, execute_academic_search
from app.tools.data_analysis import (
    CalculateStatsInput,
    ComparisonMatrixInput,
    GenerateChartInput,
    execute_calculate_statistics,
    execute_create_comparison_matrix,
    execute_generate_chart,
)
from app.tools.citation_validator import ValidateCitationsInput, execute_validate_citations


class ToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: type[BaseModel]
    handler: Callable[[Any], Any]


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._register_default_tools()

    def register(self, tool_def: ToolDefinition):
        self._tools[tool_def.name] = tool_def

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def list_schemas(self) -> List[Dict[str, Any]]:
        schemas = []
        for tool in self._tools.values():
            schemas.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.input_schema.model_json_schema(),
                }
            })
        return schemas

    def _register_default_tools(self):
        self.register(ToolDefinition(
            name="web_search",
            description="Search the web for keywords, articles, and authoritative documentation.",
            input_schema=WebSearchInput,
            handler=execute_web_search
        ))
        self.register(ToolDefinition(
            name="fetch_url",
            description="Safely fetch and extract clean text from a specific URL.",
            input_schema=FetchUrlInput,
            handler=execute_fetch_url
        ))
        self.register(ToolDefinition(
            name="extract_page_content",
            description="Extract text content and metadata from a target web URL.",
            input_schema=FetchUrlInput,
            handler=execute_fetch_url
        ))
        self.register(ToolDefinition(
            name="search_academic_sources",
            description="Search peer-reviewed academic papers via OpenAlex.",
            input_schema=AcademicSearchInput,
            handler=execute_academic_search
        ))
        self.register(ToolDefinition(
            name="search_official_sources",
            description="Search official government and standards body publications.",
            input_schema=WebSearchInput,
            handler=execute_web_search
        ))
        self.register(ToolDefinition(
            name="calculate_statistics",
            description="Calculate numerical summary statistics from data rows or dataset columns.",
            input_schema=CalculateStatsInput,
            handler=execute_calculate_statistics
        ))
        self.register(ToolDefinition(
            name="create_comparison_matrix",
            description="Generate a comparison matrix across entities and criteria.",
            input_schema=ComparisonMatrixInput,
            handler=execute_create_comparison_matrix
        ))
        self.register(ToolDefinition(
            name="generate_chart",
            description="Prepare structured chart visualization configuration and data.",
            input_schema=GenerateChartInput,
            handler=execute_generate_chart
        ))
        self.register(ToolDefinition(
            name="validate_citations",
            description="Audit report markdown citations against stored source references.",
            input_schema=ValidateCitationsInput,
            handler=execute_validate_citations
        ))


default_registry = ToolRegistry()
