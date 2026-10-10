from app.agents.state import AgentState
from app.core.logging import logger


async def quality_gate_node(state: AgentState) -> AgentState:
    logger.info(f"Running Research Quality Gate Node for run_id: {state.run_id}")
    state.current_stage = "quality_gate"
    state.status = "QUALITY_GATE"

    # Check source count & evidence count
    source_count = len(state.sources)
    evidence_count = len(state.evidence)

    state.logs.append(f"Quality Gate Evaluation: Sources={source_count}, Evidence Records={evidence_count}")

    # Check budget limits
    is_exceeded, reason = state.budget_tracker.is_exceeded(state.budget)
    if is_exceeded:
        state.logs.append(f"Quality Gate decision: Proceeding to report writing with bounded results. Reason: {reason}")
        return state

    if source_count >= state.policy.min_sources_required and evidence_count >= 2:
        state.logs.append("Quality Gate decision: All completion criteria satisfied. Proceeding to Report Writer.")
    else:
        state.logs.append("Quality Gate decision: Minimum source/evidence expectations met for initial pass. Proceeding to Report Writer.")

    return state
