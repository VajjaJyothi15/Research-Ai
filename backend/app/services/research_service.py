from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph import research_graph
from app.agents.state import AgentState
from app.core.exceptions import ResourceNotFoundException
from app.core.limits import get_budget_for_mode, get_policy_for_mode
from app.core.logging import logger
from app.services.event_manager import event_manager

from app.db.models.models import (
    Claim,
    Contradiction,
    EvidenceItem,
    Report,
    ReportVersion,
    ResearchPlan,
    ResearchRun,
    Source,
)
from app.schemas.research import ResearchCreate, ResearchPlanSchema


class ResearchService:
    def _normalize_mode(self, raw_mode: Optional[str]) -> str:
        m = (raw_mode or "standard").lower().strip()
        if m == "quick":
            return "quick"
        elif m in ["indepth", "in-depth", "deep", "academic"]:
            return "indepth"
        return "standard"

    async def create_research_run(self, db: AsyncSession, data: ResearchCreate) -> ResearchRun:
        mode = self._normalize_mode(data.mode)
        budget = get_budget_for_mode(mode, data.budget_overrides)
        policy = get_policy_for_mode(mode, data.recency_months)

        run = ResearchRun(
            question=data.question,
            objective=data.objective,
            domain=data.domain or "general",
            mode=mode,
            status="PLANNING",
            current_stage="planning",
            policy_json={"recency_months": data.recency_months},
            budget_json=budget.model_dump(),
        )
        db.add(run)
        await db.commit()
        await db.refresh(run)

        # Emit initial planning event
        event_manager.emit_event(
            run.id,
            "PLANNING",
            f"Planner Agent generating multi-step subquestions for {mode.capitalize()} Research.",
            progress_percent=10,
            status="running",
        )

        # Run planner agent to create initial plan
        init_state = AgentState(
            run_id=run.id,
            question=data.question,
            objective=data.objective,
            domain=data.domain or "general",
            mode=mode,
            policy=policy,
            budget=budget,
        )

        plan_state = await research_graph.create_plan(init_state)

        # Save research plan to database
        if plan_state.plan:
            plan_record = ResearchPlan(
                run_id=run.id,
                version=1,
                status="PENDING_APPROVAL",
                main_question=plan_state.plan.main_question,
                subquestions_json=[sq.model_dump() for sq in plan_state.plan.subquestions],
                plan_data_json=plan_state.plan.model_dump(),
            )
            db.add(plan_record)

        run.status = "PENDING_APPROVAL"
        await db.commit()
        await db.refresh(run)

        # Emit plan ready event
        subq_count = len(plan_state.plan.subquestions) if (plan_state.plan and plan_state.plan.subquestions) else 0
        event_manager.emit_event(
            run.id,
            "PLANNING",
            f"Planner Agent generated multi-step subquestions ({subq_count} steps). Awaiting approval.",
            progress_percent=15,
            status="running",
            details={"subquestions_count": subq_count, "mode": mode},
        )

        return run

    async def regenerate_plan(self, db: AsyncSession, run_id: str, feedback: str) -> ResearchPlan:
        stmt = select(ResearchRun).where(ResearchRun.id == run_id)
        res = await db.execute(stmt)
        run = res.scalar_one_or_none()
        if not run:
            raise ResourceNotFoundException("ResearchRun", run_id)

        mode = self._normalize_mode(run.mode)
        budget = get_budget_for_mode(mode, run.budget_json)
        policy = get_policy_for_mode(mode)

        # Fetch latest plan version
        stmt_plan = select(ResearchPlan).where(ResearchPlan.run_id == run_id).order_by(ResearchPlan.version.desc())
        plan_res = await db.execute(stmt_plan)
        latest_plan = plan_res.scalars().first()
        next_ver = (latest_plan.version + 1) if latest_plan else 1

        state = AgentState(
            run_id=run.id,
            question=run.question,
            objective=run.objective,
            domain=run.domain,
            mode=mode,
            policy=policy,
            budget=budget,
        )

        revised_state = await research_graph.create_plan(state, user_feedback=feedback)
        
        main_q = revised_state.plan.main_question if revised_state.plan else run.question
        subq_json = [sq.model_dump() for sq in revised_state.plan.subquestions] if revised_state.plan else []
        plan_data = revised_state.plan.model_dump() if revised_state.plan else {}

        new_plan = ResearchPlan(
            run_id=run.id,
            version=next_ver,
            status="PENDING_APPROVAL",
            main_question=main_q,
            subquestions_json=subq_json,
            plan_data_json=plan_data,
            user_feedback=feedback,
        )
        db.add(new_plan)
        run.status = "PENDING_APPROVAL"
        await db.commit()
        await db.refresh(new_plan)

        event_manager.emit_event(
            run.id,
            "PLANNING",
            f"Planner Agent revised plan (Version {next_ver}). Awaiting approval.",
            progress_percent=15,
            status="running",
            details={"version": next_ver, "mode": mode},
        )

        return new_plan

    async def approve_and_execute_plan(self, db: AsyncSession, run_id: str) -> ResearchRun:
        stmt = select(ResearchRun).where(ResearchRun.id == run_id)
        res = await db.execute(stmt)
        run = res.scalar_one_or_none()
        if not run:
            raise ResourceNotFoundException("ResearchRun", run_id)

        mode = self._normalize_mode(run.mode)
        budget = get_budget_for_mode(mode, run.budget_json)
        recency = (run.policy_json or {}).get("recency_months", 24)
        policy = get_policy_for_mode(mode, recency_months=recency)

        # Mark latest plan APPROVED
        stmt_plan = select(ResearchPlan).where(ResearchPlan.run_id == run_id).order_by(ResearchPlan.version.desc())
        plan_res = await db.execute(stmt_plan)
        latest_plan = plan_res.scalars().first()
        if latest_plan:
            latest_plan.status = "APPROVED"

        run.status = "SEARCHING"
        run.current_stage = "searching"
        await db.commit()

        # Build execution state
        plan_schema = None
        if latest_plan and latest_plan.plan_data_json:
            plan_schema = ResearchPlanSchema.model_validate(latest_plan.plan_data_json)

        state = AgentState(
            run_id=run.id,
            question=run.question,
            objective=run.objective,
            domain=run.domain,
            mode=mode,
            policy=policy,
            budget=budget,
            plan=plan_schema,
            plan_approved=True,
        )

        try:
            # Run remaining stages of graph with real event emissions
            final_state = await research_graph.execute_approved_research(state, db=db)

            # Persist sources, evidence, contradictions, report to database
            source_url_map = {}
            for s in final_state.sources:
                src_obj = Source(
                    run_id=run.id,
                    url=s.get("url"),
                    canonical_url=s.get("canonical_url"),
                    title=s.get("title", "Untitled"),
                    author=s.get("author"),
                    publication_date=s.get("publication_date"),
                    source_type=s.get("source_type", "web"),
                    domain=s.get("domain"),
                    relevance_score=s.get("relevance_score", 1.0),
                    content_text=s.get("content_text"),
                )
                db.add(src_obj)
                await db.flush()
                if s.get("url"):
                    source_url_map[s.get("url")] = src_obj.id

            for e in final_state.evidence:
                matched_source_id = source_url_map.get(e.get("source_url"))
                if not matched_source_id and source_url_map:
                    matched_source_id = list(source_url_map.values())[0]

                if matched_source_id:
                    ev_obj = EvidenceItem(
                        run_id=run.id,
                        source_id=matched_source_id,
                        claim_text=e.get("claim_text"),
                        supporting_text=e.get("supporting_text"),
                        publication_date=e.get("publication_date"),
                        evidence_type=e.get("evidence_type", "fact"),
                        confidence_score=e.get("confidence_score", 0.9),
                        verification_status=e.get("verification_status", "VERIFIED"),
                        relationship=e.get("relationship", "SUPPORTING"),
                    )
                    db.add(ev_obj)

            for c in final_state.contradictions:
                con_obj = Contradiction(
                    run_id=run.id,
                    topic=c.get("topic"),
                    claim_a=c.get("claim_a"),
                    claim_b=c.get("claim_b"),
                    description=c.get("description"),
                    resolution_status=c.get("resolution_status", "UNRESOLVED"),
                )
                db.add(con_obj)

            if final_state.markdown_report:
                rep_obj = Report(
                    run_id=run.id,
                    title=f"Research Report: {run.question}",
                    executive_summary=final_state.markdown_report[:400],
                    full_markdown=final_state.markdown_report,
                    methodology=f"Multi-source bounded retrieval and citation verification ({mode.capitalize()} mode).",
                    metadata_json={"tokens_used": final_state.budget_tracker.tokens_used, "mode": mode},
                )
                db.add(rep_obj)
                await db.flush()

                rep_ver = ReportVersion(
                    report_id=rep_obj.id,
                    version_number=1,
                    markdown_content=final_state.markdown_report,
                )
                db.add(rep_ver)

            run.status = final_state.status if final_state.status in ["COMPLETED", "PARTIAL"] else "COMPLETED"
            run.current_stage = "completed"
            run.usage_json = final_state.budget_tracker.model_dump()
            
            await db.commit()
            await db.refresh(run)

            # Emit final completed event ONLY after DB persistence succeeds
            event_manager.emit_event(
                run.id,
                "COMPLETED",
                "Research run completed and report saved successfully.",
                progress_percent=100,
                status="completed",
                details={"sources_saved": len(final_state.sources), "evidence_saved": len(final_state.evidence), "mode": mode},
            )
            return run

        except Exception as e:
            logger.error(f"Error during research execution for run {run_id}: {e}", exc_info=True)
            run.status = "FAILED"
            run.current_stage = "failed"
            await db.commit()

            event_manager.emit_event(
                run_id,
                "FAILED",
                f"Research failed: {str(e)}",
                progress_percent=0,
                status="failed",
            )
            raise


research_service = ResearchService()

