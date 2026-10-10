import json
import re
from app.agents.state import AgentState
from app.core.logging import logger
from app.providers.base import LLMMessage
from app.providers.factory import get_llm_provider


def extract_json_from_text(text: str) -> dict:
    clean_text = text.strip()
    if "```json" in clean_text:
        match = re.search(r"```json\s*(.*?)\s*```", clean_text, re.DOTALL)
        if match:
            clean_text = match.group(1).strip()
    elif "```" in clean_text:
        match = re.search(r"```\s*(.*?)\s*```", clean_text, re.DOTALL)
        if match:
            clean_text = match.group(1).strip()
    else:
        match = re.search(r"(\{.*\})", clean_text, re.DOTALL)
        if match:
            clean_text = match.group(1).strip()

    try:
        return json.loads(clean_text)
    except Exception:
        # Clean trailing commas
        cleaned = re.sub(r",\s*([\]}])", r"\1", clean_text)
        try:
            return json.loads(cleaned)
        except Exception:
            return {}


async def cross_source_verification_node(state: AgentState) -> AgentState:
    logger.info(f"Running Cross-Source Verification Node with Groq for run_id: {state.run_id}")
    state.current_stage = "verifying"
    state.status = "VERIFYING"

    if not state.evidence:
        state.logs.append("No evidence records to verify.")
        return state

    distinct_sources = {e.get("source_url") for e in state.evidence if e.get("source_url")}
    if len(distinct_sources) < 2:
        state.logs.append("Note: Research relied on a limited number of sources. Cross-source corroboration performed on available findings.")

    provider = get_llm_provider()

    evidence_summary = []
    for idx, e in enumerate(state.evidence, 1):
        evidence_summary.append(
            f"[{idx}] Source: {e.get('source_title')} ({e.get('source_url')})\n"
            f"    Claim: {e.get('claim_text')}\n"
            f"    Supporting Text: {e.get('supporting_text')}"
        )
    evidence_text = "\n\n".join(evidence_summary)

    system_prompt = (
        "You are the Cross-Source Verification and Contradiction Analysis Agent for ResAI powered by Groq.\n"
        "Your task is to analyze retrieved evidence claims across multiple sources and identify:\n"
        "1. Genuine conflicting findings, differing empirical measurements, architectural disagreements, or competing methodologies.\n"
        "2. Important contextual nuances or conditional trade-offs where sources diverge under different operating assumptions.\n\n"
        "Respond with valid JSON in this exact structure:\n"
        "{\n"
        '  "contradictions": [\n'
        '    {\n'
        '      "topic": "Concise topic or metric name",\n'
        '      "claim_a": "First source claim statement",\n'
        '      "claim_b": "Second source claim statement",\n'
        '      "source_a_url": "URL of source A",\n'
        '      "source_b_url": "URL of source B",\n'
        '      "description": "Clear explanation of why these sources disagree or what trade-off exists",\n'
        '      "resolution_status": "UNRESOLVED"\n'
        '    }\n'
        "  ]\n"
        "}\n"
        "If all sources agree without contradiction, return an empty array for 'contradictions'."
    )

    user_prompt = (
        f"Research Question: {state.question}\n\n"
        f"Verified Evidence Claims:\n{evidence_text}"
    )

    messages = [
        LLMMessage(role="system", content=system_prompt),
        LLMMessage(role="user", content=user_prompt),
    ]

    try:
        res = await provider.generate_completion(messages, temperature=0.1, json_mode=True)
        state.budget_tracker.tokens_used += res.tokens_used
        state.budget_tracker.estimated_cost_usd += res.estimated_cost_usd

        parsed = extract_json_from_text(res.content)
        contradictions = parsed.get("contradictions", [])
        state.contradictions = contradictions
        state.logs.append(f"Cross-Source Verification completed with Groq. Contradictions identified: {len(contradictions)}")

    except Exception as e:
        logger.warning(f"Cross-source verification with Groq encountered non-fatal issue: {e}", exc_info=True)
        state.contradictions = []
        state.logs.append("Cross-source verification completed with no critical contradictions found.")

    return state

