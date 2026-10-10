import asyncio
import json
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.core.exceptions import ResourceNotFoundException
from app.db.models.models import ResearchRun
from app.schemas.research import ResearchCreate, ResearchRunResponse
from app.services.event_manager import event_manager
from app.services.research_service import research_service

router = APIRouter()


@router.post("", response_model=ResearchRunResponse, status_code=status.HTTP_201_CREATED)
async def create_research(
    data: ResearchCreate,
    db: AsyncSession = Depends(get_db_session),
):
    """Creates a new research run and generates an initial research plan."""
    run = await research_service.create_research_run(db, data)
    return run


@router.get("", response_model=List[ResearchRunResponse])
async def list_research_runs(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db_session),
):
    """Lists recent research runs."""
    stmt = select(ResearchRun).order_by(ResearchRun.created_at.desc()).limit(limit).offset(offset)
    res = await db.execute(stmt)
    return res.scalars().all()


@router.delete("", status_code=status.HTTP_200_OK)
async def clear_research_history(
    db: AsyncSession = Depends(get_db_session),
):
    """Clears all saved research history and cascaded artifacts."""
    stmt = select(ResearchRun)
    res = await db.execute(stmt)
    runs = res.scalars().all()
    count = len(runs)
    for run in runs:
        await db.delete(run)
    await db.commit()
    return {"message": f"Successfully cleared {count} research sessions.", "deleted_count": count}


@router.delete("/{research_id}", status_code=status.HTTP_200_OK)
async def delete_research_run(
    research_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    """Deletes a specific research run and all its related records."""
    stmt = select(ResearchRun).where(ResearchRun.id == research_id)
    res = await db.execute(stmt)
    run = res.scalar_one_or_none()
    if not run:
        raise ResourceNotFoundException("ResearchRun", research_id)
    await db.delete(run)
    await db.commit()
    return {"message": "Research run deleted successfully", "research_id": research_id}



@router.get("/{research_id}", response_model=ResearchRunResponse)
async def get_research_run(
    research_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    """Gets research run details by ID."""
    stmt = select(ResearchRun).where(ResearchRun.id == research_id)
    res = await db.execute(stmt)
    run = res.scalar_one_or_none()
    if not run:
        raise ResourceNotFoundException("ResearchRun", research_id)
    return run


@router.post("/{research_id}/cancel")
async def cancel_research_run(
    research_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    """Cancels a running research task."""
    stmt = select(ResearchRun).where(ResearchRun.id == research_id)
    res = await db.execute(stmt)
    run = res.scalar_one_or_none()
    if not run:
        raise ResourceNotFoundException("ResearchRun", research_id)

    run.status = "CANCELLED"
    run.current_stage = "cancelled"
    await db.commit()

    event_manager.emit_event(
        research_id,
        "CANCELLED",
        "Research run was cancelled by user.",
        progress_percent=0,
        status="cancelled",
    )

    return {"message": "Research run cancelled successfully", "research_id": research_id}


@router.post("/{research_id}/rerun", response_model=ResearchRunResponse)
async def rerun_research(
    research_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    """Reruns a saved research question to discover fresh evidence."""
    stmt = select(ResearchRun).where(ResearchRun.id == research_id)
    res = await db.execute(stmt)
    run = res.scalar_one_or_none()
    if not run:
        raise ResourceNotFoundException("ResearchRun", research_id)

    new_create_data = ResearchCreate(
        question=run.question,
        objective=run.objective,
        domain=run.domain,
        mode=run.mode,
    )
    new_run = await research_service.create_research_run(db, new_create_data)
    return new_run


@router.get("/{research_id}/events")
async def stream_research_events(
    research_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    """Server-Sent Events (SSE) endpoint streaming real execution events with history replay and reconnection support."""
    stmt = select(ResearchRun).where(ResearchRun.id == research_id)
    res = await db.execute(stmt)
    run = res.scalar_one_or_none()
    if not run:
        raise ResourceNotFoundException("ResearchRun", research_id)

    async def event_generator():
        queue = event_manager.subscribe(research_id)
        try:
            # 1. Replay in-memory event history
            history = event_manager.get_history(research_id)

            # If pending approval, stream initial planning event and finish
            if run.status == "PENDING_APPROVAL":
                if history:
                    for evt in history:
                        yield f"event: stage_update\ndata: {json.dumps(evt)}\n\n"
                else:
                    init_evt = {
                        "research_id": research_id,
                        "stage": "PLANNING",
                        "stage_label": "Research planning",
                        "stage_index": 1,
                        "total_stages": 7,
                        "progress_percent": 15,
                        "message": "Planner Agent generated multi-step subquestions. Awaiting approval.",
                        "status": "running",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                    yield f"event: stage_update\ndata: {json.dumps(init_evt)}\n\n"
                return

            if history:
                for evt in history:
                    yield f"event: stage_update\ndata: {json.dumps(evt)}\n\n"
            else:
                # If server restarted or historical run loaded from DB, reconstruct state
                if run.status in ["COMPLETED", "PARTIAL"]:
                    historical_stages = [
                        ("PLANNING", "Planner Agent generated multi-step subquestions.", 15, "completed"),
                        ("SEARCHING", "Web and academic search queries completed.", 35, "completed"),
                        ("EXTRACTING", "Evidence extraction completed from source pages.", 55, "completed"),
                        ("VERIFYING", "Cross-source verification and contradiction check completed.", 70, "completed"),
                        ("ANALYZING", "Comparison matrix and benchmark statistics calculated.", 85, "completed"),
                        ("WRITING", "Report Writer Agent generated evidence report.", 95, "completed"),
                        ("COMPLETED", "Research run completed and report saved successfully.", 100, "completed"),
                    ]
                    for stg, msg, pct, st in historical_stages:
                        payload = {
                            "research_id": research_id,
                            "stage": stg,
                            "stage_label": stg.replace("_", " ").title(),
                            "stage_index": 7 if stg == "COMPLETED" else 1,
                            "total_stages": 7,
                            "progress_percent": pct,
                            "message": msg,
                            "status": st,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                        yield f"event: stage_update\ndata: {json.dumps(payload)}\n\n"
                    return
                elif run.status == "FAILED":
                    fail_evt = {
                        "research_id": research_id,
                        "stage": "FAILED",
                        "stage_label": "Execution failed",
                        "stage_index": 0,
                        "total_stages": 7,
                        "progress_percent": 0,
                        "message": "Research execution failed.",
                        "status": "failed",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                    yield f"event: stage_update\ndata: {json.dumps(fail_evt)}\n\n"
                    return
                elif run.status == "CANCELLED":
                    cancel_evt = {
                        "research_id": research_id,
                        "stage": "CANCELLED",
                        "stage_label": "Cancelled",
                        "stage_index": 0,
                        "total_stages": 7,
                        "progress_percent": 0,
                        "message": "Research run cancelled by user.",
                        "status": "cancelled",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                    yield f"event: stage_update\ndata: {json.dumps(cancel_evt)}\n\n"
                    return

            # 2. If already in terminal state, we are done
            if run.status in ["COMPLETED", "PARTIAL", "FAILED", "CANCELLED"]:
                return
            if history and history[-1].get("status") in ["completed", "failed", "cancelled"]:
                return

            # 3. Stream live events from the subscriber queue while running
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=2.0)
                    yield f"event: stage_update\ndata: {json.dumps(event)}\n\n"
                    if event.get("status") in ["completed", "failed", "cancelled"]:
                        break
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
                except (asyncio.CancelledError, GeneratorExit):
                    break

        except (asyncio.CancelledError, GeneratorExit):
            pass
        finally:
            event_manager.unsubscribe(research_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
