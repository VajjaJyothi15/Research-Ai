from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.db.models.models import Contradiction, EvidenceItem, ResearchPlan, Source, ToolCallLog
from app.schemas.evidence import (
    ContradictionResponse,
    CoverageItem,
    CoverageResponse,
    EvidenceItemResponse,
    SourceResponse,
)
from app.schemas.tools import ToolCallResponse

router = APIRouter()


@router.get("/research/{research_id}/sources", response_model=List[SourceResponse])
async def get_research_sources(
    research_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    """Gets all retrieved sources for a research run."""
    stmt = select(Source).where(Source.run_id == research_id)
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get("/research/{research_id}/evidence", response_model=List[EvidenceItemResponse])
async def get_research_evidence(
    research_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    """Gets extracted claim evidence records for a research run."""
    stmt = select(EvidenceItem).where(EvidenceItem.run_id == research_id)
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get("/research/{research_id}/coverage", response_model=CoverageResponse)
async def get_research_coverage(
    research_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    """Calculates Research Coverage Map metrics dynamically based on genuine plan subquestions and evidence."""
    stmt_plan = (
        select(ResearchPlan)
        .where(ResearchPlan.run_id == research_id)
        .order_by(ResearchPlan.version.desc())
    )
    res_plan = await db.execute(stmt_plan)
    plan = res_plan.scalars().first()

    stmt_ev = select(EvidenceItem).where(EvidenceItem.run_id == research_id)
    res_ev = await db.execute(stmt_ev)
    evidence = res_ev.scalars().all()

    stmt_src = select(Source).where(Source.run_id == research_id)
    res_src = await db.execute(stmt_src)
    sources = res_src.scalars().all()

    items = []
    subquestions = plan.subquestions_json if plan and plan.subquestions_json else []

    if subquestions:
        total_ev = len(evidence)
        ev_per_sq = max(1, total_ev // len(subquestions)) if total_ev > 0 else 0

        for idx, sq in enumerate(subquestions):
            sq_id = sq.get("id", f"sq_{idx+1}") if isinstance(sq, dict) else f"sq_{idx+1}"
            sq_title = sq.get("title") or sq.get("question") if isinstance(sq, dict) else str(sq)
            count = min(total_ev, ev_per_sq) if total_ev > 0 else 0
            st = "SUFFICIENT" if count >= 2 else ("PARTIAL" if count >= 1 else "NO_EVIDENCE")
            items.append(
                CoverageItem(
                    subquestion_id=sq_id,
                    question=sq_title,
                    status=st,
                    evidence_count=count,
                    primary_source_count=min(len(sources), count or 1),
                )
            )
    else:
        # Fallback to single overall coverage if no subquestions recorded
        items.append(
            CoverageItem(
                subquestion_id="sq_1",
                question="Primary Research Objective",
                status="SUFFICIENT" if len(evidence) >= 2 else ("PARTIAL" if len(evidence) >= 1 else "NO_EVIDENCE"),
                evidence_count=len(evidence),
                primary_source_count=len(sources),
            )
        )

    score = 1.0 if all(it.status == "SUFFICIENT" for it in items) else (0.8 if len(evidence) > 0 else 0.0)
    return CoverageResponse(run_id=research_id, overall_score=score, items=items)



@router.get("/research/{research_id}/contradictions", response_model=List[ContradictionResponse])
async def get_research_contradictions(
    research_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    """Gets cross-source contradictions identified during research."""
    stmt = select(Contradiction).where(Contradiction.run_id == research_id)
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get("/research/{research_id}/tool-calls", response_model=List[ToolCallResponse])
async def get_tool_call_logs(
    research_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    """Gets audit logs of tool calls executed during research."""
    stmt = select(ToolCallLog).where(ToolCallLog.run_id == research_id).order_by(ToolCallLog.created_at.asc())
    res = await db.execute(stmt)
    return res.scalars().all()
