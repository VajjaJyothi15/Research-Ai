import json
import re
from app.agents.state import AgentState
from app.core.logging import logger
from app.providers.base import LLMMessage
from app.providers.factory import get_llm_provider
from app.tools.dispatcher import dispatcher


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


async def analytical_node(state: AgentState, db=None) -> AgentState:
    logger.info(f"Running Analytical Node with Groq for run_id: {state.run_id}")
    state.current_stage = "analyzing"
    state.status = "ANALYZING"

    analysis_out = {}
    provider = get_llm_provider()

    evidence_summary = []
    for idx, e in enumerate(state.evidence, 1):
        evidence_summary.append(
            f"Evidence {idx}: Claim='{e.get('claim_text')}', SupportingText='{e.get('supporting_text')}', SourceURL='{e.get('source_url')}'"
        )
    evidence_text = "\n".join(evidence_summary) if evidence_summary else "No verified evidence items recorded."

    sources_summary = []
    for idx, s in enumerate(state.sources, 1):
        sources_summary.append(f"[{idx}] {s.get('title')} ({s.get('url')})")
    sources_text = "\n".join(sources_summary) if sources_summary else "No sources."

    system_prompt = (
        "You are the Analytical & Quantitative Synthesis Agent for ResAI, an evidence-grounded research platform powered by Groq.\n"
        "Your goal is to analyze the research question and retrieved evidence, and produce a structured comparison matrix and quantitative benchmark summary.\n\n"
        "RULES:\n"
        "1. Extract the actual entities, models, methods, or architectures mentioned in the research question or evidence.\n"
        "2. Formulate 3-4 meaningful evaluation criteria relevant to the topic (e.g. Accuracy, Latency, Memory Safety, Computational Cost, Strengths/Weaknesses).\n"
        "3. Populate the comparison matrix strictly with findings from the evidence. Include citation numbers like [1], [2] in cells where applicable.\n"
        "4. If a measurement or comparison is not reported in the evidence, use 'Not reported' or 'Insufficient evidence'. NEVER invent false numbers or benchmarks.\n"
        "5. Output valid JSON in this exact structure:\n"
        "{\n"
        '  "topic": "Concise topic title",\n'
        '  "headers": ["Entity", "Criterion 1", "Criterion 2", "Criterion 3"],\n'
        '  "rows": [\n'
        '    {"Entity": "...", "Criterion 1": "... [1]", "Criterion 2": "...", "Criterion 3": "..."}\n'
        '  ],\n'
        '  "quantitative_metrics": [\n'
        '    {"metric": "...", "score": 90.0, "unit": "%"}\n'
        '  ]\n'
        "}"
    )

    user_prompt = (
        f"Research Question: {state.question}\n"
        f"Domain: {state.domain}\n\n"
        f"Retrieved Sources:\n{sources_text}\n\n"
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
        headers = parsed.get("headers", ["Entity", "Performance", "Trade-offs", "Source Evidence"])
        rows = parsed.get("rows", [])
        topic = parsed.get("topic", state.question)

        analysis_out["comparison_matrix"] = {
            "topic": topic,
            "headers": headers,
            "rows": rows,
        }

        # Log matrix tool call
        try:
            matrix_res = await dispatcher.dispatch(
                tool_name="create_comparison_matrix",
                arguments={
                    "topic": topic,
                    "entities": [r.get("Entity", f"Approach {i+1}") for i, r in enumerate(rows)] or [state.question[:30]],
                    "criteria": headers[1:] if len(headers) > 1 else ["Analysis"],
                },
                run_id=state.run_id,
                stage="analyzing",
                db=db,
            )
        except Exception as e:
            logger.warning(f"Dispatcher log comparison matrix failed: {e}")

        # Process quantitative metrics if available
        metrics = parsed.get("quantitative_metrics", [])
        if metrics:
            chart_data = [{"metric": m.get("metric", "Metric"), "score": float(m.get("score", 0))} for m in metrics]
            analysis_out["chart"] = {
                "title": f"Quantitative Findings: {state.question[:50]}",
                "chart_type": "bar",
                "x_axis_key": "metric",
                "y_axis_key": "score",
                "chart_data": chart_data,
            }

            try:
                numeric_data = [{m.get("metric", f"metric_{i}"): float(m.get("score", 0))} for i, m in enumerate(metrics)]
                stats_res = await dispatcher.dispatch(
                    tool_name="calculate_statistics",
                    arguments={
                        "data": numeric_data,
                        "selected_columns": [m.get("metric", f"metric_{i}") for i, m in enumerate(metrics)],
                    },
                    run_id=state.run_id,
                    stage="analyzing",
                    db=db,
                )
                analysis_out["statistics"] = stats_res.model_dump()
            except Exception as se:
                logger.warning(f"Calculate statistics failed: {se}")

    except Exception as e:
        logger.warning(f"Analytical node Groq execution encountered issue: {e}", exc_info=True)
        if "comparison_matrix" not in analysis_out:
            analysis_out["comparison_matrix"] = {
                "topic": state.question,
                "headers": ["Entity", "Key Finding", "Source Reference"],
                "rows": [
                    {"Entity": e.get("claim_text", "")[:40], "Key Finding": e.get("supporting_text", "")[:80], "Source Reference": "[1]"}
                    for e in state.evidence[:3]
                ] if state.evidence else [],
            }

    state.analysis_results = analysis_out
    state.logs.append("Analytical Agent completed evidence synthesis.")
    return state

