from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.nodes.analyst import analytical_node
from app.agents.nodes.citation_auditor import citation_audit_node
from app.agents.nodes.extractor import evidence_extraction_node
from app.agents.nodes.planner import plan_research_node
from app.agents.nodes.quality_gate import quality_gate_node
from app.agents.nodes.researcher import search_and_retrieval_node
from app.agents.nodes.verifier import cross_source_verification_node
from app.agents.nodes.writer import report_writer_node
from app.agents.state import AgentState
from app.core.logging import logger
from app.services.event_manager import event_manager


class ResearchWorkflowGraph:
    async def create_plan(self, state: AgentState, user_feedback: Optional[str] = None, feedback: Optional[str] = None) -> AgentState:
        """Executes Stage 1 & Stage 2 to generate/revise research plan."""
        fb = user_feedback or feedback
        state = await plan_research_node(state, user_feedback=fb)
        return state

    async def execute_approved_research(self, state: AgentState, db: Optional[AsyncSession] = None) -> AgentState:
        """Executes Stage 2 through Stage 7 after user plan approval with real-time SSE progress events."""
        logger.info(f"Starting execution of approved research graph for run_id: {state.run_id}")
        
        # 1. Search & Retrieval (Web and academic search)
        event_manager.emit_event(
            state.run_id,
            "SEARCHING",
            "Executing web_search and academic_search queries.",
            progress_percent=25,
            status="running",
        )
        state = await search_and_retrieval_node(state, db=db)
        event_manager.emit_event(
            state.run_id,
            "SEARCHING",
            f"Search complete. Discovered {len(state.sources)} authoritative sources.",
            progress_percent=35,
            status="running",
            details={"sources_count": len(state.sources)},
        )

        # 2. Evidence Extraction
        event_manager.emit_event(
            state.run_id,
            "EXTRACTING",
            "Converting retrieved pages into evidence records.",
            progress_percent=42,
            status="running",
        )
        state = await evidence_extraction_node(state)
        event_manager.emit_event(
            state.run_id,
            "EXTRACTING",
            f"Evidence extraction complete. Extracted {len(state.evidence)} verified claims.",
            progress_percent=55,
            status="running",
            details={"evidence_count": len(state.evidence)},
        )

        # 3. Cross-Source Verification
        event_manager.emit_event(
            state.run_id,
            "VERIFYING",
            "Performing cross-source contradiction check.",
            progress_percent=60,
            status="running",
        )
        state = await cross_source_verification_node(state)
        event_manager.emit_event(
            state.run_id,
            "VERIFYING",
            f"Cross-source verification complete ({len(state.contradictions)} contradictions identified).",
            progress_percent=70,
            status="running",
            details={"contradictions_count": len(state.contradictions)},
        )

        # 4. Analytical Agent
        event_manager.emit_event(
            state.run_id,
            "ANALYZING",
            "Generating comparison matrix and statistics.",
            progress_percent=75,
            status="running",
        )
        state = await analytical_node(state, db=db)

        # 5. Quality Gate
        state = await quality_gate_node(state)
        event_manager.emit_event(
            state.run_id,
            "ANALYZING",
            "Comparison matrix and quantitative benchmarks validated.",
            progress_percent=85,
            status="running",
        )

        # 6. Report Writer & Citation Audit
        event_manager.emit_event(
            state.run_id,
            "WRITING",
            "Report Writer Agent generating markdown report.",
            progress_percent=90,
            status="running",
        )
        state = await report_writer_node(state)
        state = await citation_audit_node(state, db=db)
        event_manager.emit_event(
            state.run_id,
            "WRITING",
            "Report generated and inline citations verified.",
            progress_percent=95,
            status="running",
        )

        return state


research_graph = ResearchWorkflowGraph()
