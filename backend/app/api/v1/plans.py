from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.core.exceptions import ResourceNotFoundException
from app.db.models.models import ResearchPlan, ResearchRun
from app.schemas.research import (
    PlanEditRequest,
    PlanRegenerateRequest,
    ResearchPlanResponse,
    ResearchRunResponse,
)
from app.services.research_service import research_service

router = APIRouter()


@router.get("/research/{research_id}/plan", response_model=ResearchPlanResponse)
async def get_latest_plan(
    research_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    """Gets the latest generated research plan for user review."""
    stmt = (
        select(ResearchPlan)
        .where(ResearchPlan.run_id == research_id)
        .order_by(ResearchPlan.version.desc())
    )
    res = await db.execute(stmt)
    plan = res.scalars().first()
    if not plan:
        raise ResourceNotFoundException("ResearchPlan", research_id)
    return plan


@router.post("/research/{research_id}/plan/regenerate", response_model=ResearchPlanResponse)
async def regenerate_plan(
    research_id: str,
    body: PlanRegenerateRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Regenerates the research plan using user feedback."""
    plan = await research_service.regenerate_plan(db, research_id, body.user_feedback)
    return plan


@router.patch("/research/{research_id}/plan", response_model=ResearchPlanResponse)
async def edit_plan(
    research_id: str,
    body: PlanEditRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Edits subquestions or main question in the current draft plan."""
    stmt = (
        select(ResearchPlan)
        .where(ResearchPlan.run_id == research_id)
        .order_by(ResearchPlan.version.desc())
    )
    res = await db.execute(stmt)
    plan = res.scalars().first()
    if not plan:
        raise ResourceNotFoundException("ResearchPlan", research_id)

    if body.main_question:
        plan.main_question = body.main_question
    if body.subquestions is not None:
        plan.subquestions_json = body.subquestions

    await db.commit()
    await db.refresh(plan)
    return plan


@router.post("/research/{research_id}/plan/approve", response_model=ResearchRunResponse)
async def approve_and_start_research(
    research_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    """Approves the plan and triggers execution of the remaining research workflow."""
    run = await research_service.approve_and_execute_plan(db, research_id)
    return run
