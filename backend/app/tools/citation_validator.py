import re
from typing import List
from pydantic import BaseModel, Field


class ValidateCitationsInput(BaseModel):
    markdown_text: str = Field(..., description="Report markdown content")
    available_source_ids: List[str] = Field(default_factory=list, description="IDs of valid retrieved sources")


class CitationAuditResult(BaseModel):
    is_valid: bool
    total_citations_found: int
    resolved_citations_count: int
    unsupported_claims: List[str]
    missing_source_references: List[str]


async def execute_validate_citations(input_data: ValidateCitationsInput | dict) -> CitationAuditResult:
    if isinstance(input_data, dict):
        input_data = ValidateCitationsInput(**input_data)
    text = input_data.markdown_text
    
    # Regex to extract in-text numeric citations e.g. [1], [2], [1][3]
    citation_matches = re.findall(r"\[(\d+)\]", text)
    unique_citations = sorted(list(set(int(c) for c in citation_matches)))
    
    # Extract references list items
    reference_lines = [line for line in text.split("\n") if re.match(r"^\s*-\s*\[\d+\]", line)]
    ref_count = len(reference_lines)

    missing = []
    for citation in unique_citations:
        if citation > ref_count and ref_count > 0:
            missing.append(f"Citation [{citation}] has no matching reference entry.")

    # Check for unreferenced statements
    unsupported = []
    sentences = re.split(r"(?<=[.!?]) +", text)
    for stmt in sentences:
        if any(kw in stmt.lower() for kw in ["statistically proven", "studies show", "data confirms", "benchmarks indicate"]):
            if not re.search(r"\[\d+\]", stmt):
                unsupported.append(stmt.strip())

    is_valid = len(missing) == 0 and len(unsupported) == 0

    return CitationAuditResult(
        is_valid=is_valid,
        total_citations_found=len(unique_citations),
        resolved_citations_count=len(unique_citations) - len(missing),
        unsupported_claims=unsupported[:5],
        missing_source_references=missing,
    )
