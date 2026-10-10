from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from app.core.config import settings


class ResearchBudget(BaseModel):
    max_iterations: int = Field(default_factory=lambda: settings.MAX_RESEARCH_ITERATIONS)
    max_tool_calls: int = Field(default_factory=lambda: settings.MAX_TOOL_CALLS)
    max_sources: int = Field(default_factory=lambda: settings.MAX_SOURCES)
    max_tokens: int = 100000
    estimated_cost_usd_limit: float = 2.00
    timeout_seconds: int = Field(default_factory=lambda: settings.RESEARCH_TIMEOUT_SECONDS)


class ResearchPolicy(BaseModel):
    mode: str = "standard"  # quick, standard, indepth
    recency_months: int = 24
    preferred_domains: list[str] = []
    excluded_domains: list[str] = []
    min_sources_required: int = 3
    prioritize_primary_sources: bool = True
    allow_academic_papers: bool = True


def get_budget_for_mode(mode: str, overrides: Optional[Dict[str, Any]] = None) -> ResearchBudget:
    m = (mode or "standard").lower()
    if m == "quick":
        defaults = {
            "max_iterations": 1,
            "max_tool_calls": 6,
            "max_sources": 4,
            "max_tokens": 50000,
            "estimated_cost_usd_limit": 1.00,
            "timeout_seconds": 120,
        }
    elif m in ["indepth", "deep", "academic"]:
        defaults = {
            "max_iterations": 3,
            "max_tool_calls": 20,
            "max_sources": 15,
            "max_tokens": 150000,
            "estimated_cost_usd_limit": 3.00,
            "timeout_seconds": 400,
        }
    else:  # standard
        defaults = {
            "max_iterations": 2,
            "max_tool_calls": 12,
            "max_sources": 8,
            "max_tokens": 100000,
            "estimated_cost_usd_limit": 2.00,
            "timeout_seconds": 240,
        }
    
    if overrides:
        defaults.update(overrides)
    return ResearchBudget(**defaults)


def get_policy_for_mode(mode: str, recency_months: int = 24) -> ResearchPolicy:
    m = (mode or "standard").lower()
    norm_mode = "quick" if m == "quick" else ("indepth" if m in ["indepth", "deep", "academic"] else "standard")
    min_sources = 2 if norm_mode == "quick" else (5 if norm_mode == "indepth" else 3)
    return ResearchPolicy(
        mode=norm_mode,
        recency_months=recency_months,
        min_sources_required=min_sources,
        allow_academic_papers=True,
        prioritize_primary_sources=True,
    )


class BudgetTracker(BaseModel):
    iterations_used: int = 0
    tool_calls_used: int = 0
    sources_fetched: int = 0
    tokens_used: int = 0
    estimated_cost_usd: float = 0.0

    def is_exceeded(self, budget: ResearchBudget) -> tuple[bool, str]:
        if self.iterations_used >= budget.max_iterations:
            return True, f"Max iterations ({budget.max_iterations}) reached."
        if self.tool_calls_used >= budget.max_tool_calls:
            return True, f"Max tool calls ({budget.max_tool_calls}) reached."
        if self.sources_fetched >= budget.max_sources:
            return True, f"Max sources ({budget.max_sources}) reached."
        if self.tokens_used >= budget.max_tokens:
            return True, f"Max token budget ({budget.max_tokens}) reached."
        if self.estimated_cost_usd >= budget.estimated_cost_usd_limit:
            return True, f"Max cost limit (${budget.estimated_cost_usd_limit:.2f}) reached."
        return False, ""

