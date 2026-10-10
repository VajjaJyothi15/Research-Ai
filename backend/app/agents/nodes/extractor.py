import asyncio
import json
import re
from datetime import datetime, timezone
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
        cleaned = re.sub(r",\s*([\]}])", r"\1", clean_text)
        try:
            return json.loads(cleaned)
        except Exception:
            return {}


async def extract_claims_for_source(provider, source: dict, question: str, system_prompt: str):
    content_snippet = (source.get("content_text") or "")[:2500]
    if not content_snippet:
        return [], 0, 0.0

    user_prompt = (
        f"Research Question: {question}\n"
        f"Source Title: {source.get('title')}\n"
        f"Source URL: {source.get('url')}\n"
        f"Publication Date: {source.get('publication_date')}\n\n"
        f"Source Content Excerpt:\n{content_snippet}"
    )
    messages = [
        LLMMessage(role="system", content=system_prompt),
        LLMMessage(role="user", content=user_prompt),
    ]

    try:
        res = await provider.generate_completion(messages, temperature=0.1, json_mode=True)
        parsed = extract_json_from_text(res.content)
        claims_extracted = parsed.get("claims", [])
        evidence_list = []
        for c in claims_extracted:
            claim_txt = c.get("claim_text")
            if not claim_txt:
                continue
            evidence_rec = {
                "source_url": source.get("url"),
                "source_title": source.get("title"),
                "claim_text": claim_txt,
                "supporting_text": c.get("supporting_text") or content_snippet[:250],
                "publication_date": source.get("publication_date"),
                "retrieval_timestamp": datetime.now(timezone.utc).isoformat(),
                "evidence_type": c.get("evidence_type", "fact"),
                "confidence_score": float(c.get("confidence_score", 0.9)),
                "verification_status": "VERIFIED",
                "relationship": c.get("relationship", "SUPPORTING"),
            }
            evidence_list.append(evidence_rec)
        return evidence_list, res.tokens_used, res.estimated_cost_usd
    except Exception as e:
        logger.warning(f"Evidence extraction failed for source {source.get('url')}: {e}")
        return [], 0, 0.0


async def evidence_extraction_node(state: AgentState) -> AgentState:
    logger.info(f"Running Evidence Extraction Node for run_id: {state.run_id}")
    state.current_stage = "extracting"
    state.status = "EXTRACTING"

    if not state.sources:
        state.logs.append("No sources available for evidence extraction.")
        return state

    provider = get_llm_provider()
    system_prompt = (
        "You are the Evidence Extraction Agent for ResAI, an autonomous research system powered by Groq.\n"
        "Your task is to analyze retrieved source content and extract genuine, verifiable factual claims and statistics in valid JSON format.\n"
        "Format your output strictly as a JSON object:\n"
        "{\n"
        '  "claims": [\n'
        '    {\n'
        '      "claim_text": "Clear statement of the factual finding or metric",\n'
        '      "supporting_text": "Direct excerpt or evidence snippet from the source text",\n'
        '      "evidence_type": "fact",\n'
        '      "confidence_score": 0.95,\n'
        '      "relationship": "SUPPORTING"\n'
        '    }\n'
        "  ]\n"
        "}\n"
        "Allowed evidence_type values: 'fact', 'stat', 'quote', 'opinion', 'calculation'.\n"
        "Allowed relationship values: 'SUPPORTING', 'CONTRADICTING'."
    )

    sources_to_process = state.sources[: state.budget.max_sources]
    sem = asyncio.Semaphore(1)

    async def sem_extract(src):
        async with sem:
            await asyncio.sleep(0.1)
            return await extract_claims_for_source(provider, src, state.question, system_prompt)

    tasks = [sem_extract(s) for s in sources_to_process]

    results = await asyncio.gather(*tasks)
    for evidence_list, tokens, cost in results:
        state.evidence.extend(evidence_list)
        state.budget_tracker.tokens_used += tokens
        state.budget_tracker.estimated_cost_usd += cost

    state.logs.append(f"Evidence Extraction completed. Total evidence items extracted: {len(state.evidence)}")
    return state
