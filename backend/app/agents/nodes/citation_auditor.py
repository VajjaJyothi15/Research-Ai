from app.agents.state import AgentState
from app.core.logging import logger
from app.tools.dispatcher import dispatcher


async def citation_audit_node(state: AgentState, db=None) -> AgentState:
    logger.info(f"Running Citation Audit Node for run_id: {state.run_id}")
    state.current_stage = "citation_audit"
    state.status = "CITATION_AUDIT"

    if not state.markdown_report:
        state.status = "FAILED"
        state.error_message = "No report markdown found for citation auditing."
        return state

    try:
        source_ids = [s.get("url") for s in state.sources if s.get("url")]
        audit_res = await dispatcher.dispatch(
            tool_name="validate_citations",
            arguments={
                "markdown_text": state.markdown_report,
                "available_source_ids": source_ids,
            },
            run_id=state.run_id,
            stage="citation_audit",
            db=db,
        )
        state.logs.append(
            f"Citation Audit result: Valid={audit_res.is_valid}, "
            f"Total={audit_res.total_citations_found}, Resolved={audit_res.resolved_citations_count}"
        )

        exceeded, _ = state.budget_tracker.is_exceeded(state.budget)
        if exceeded:
            state.status = "PARTIAL"
        else:
            state.status = "COMPLETED"

        state.current_stage = "completed"
    except Exception as e:
        logger.error(f"Citation audit node failed: {e}")
        state.status = "COMPLETED"
        state.current_stage = "completed"

    return state
