import json
import re
from typing import Optional
from app.agents.state import AgentState
from app.core.exceptions import LLMProviderException
from app.core.logging import logger
from app.providers.base import LLMMessage
from app.providers.factory import get_llm_provider
from app.schemas.research import ResearchPlanSchema, SubQuestionSchema


def generate_short_title(question: str, idx: int) -> str:
    """Generates a meaningful 3-5 word title for a research step."""
    if not question:
        return f"Investigate Key Aspect {idx + 1}"

    cleaned = re.sub(r"^(what (are|is)|how (do|does|can|will)|explain|describe|analyze|investigate|evaluate)\s+(the|a|an)?\s*", "", question, flags=re.IGNORECASE)
    cleaned = re.sub(r"\?+$", "", cleaned).strip()

    if "foundation" in question.lower() or "concept" in question.lower() or "architect" in question.lower():
        return "Understand Core Foundations"
    if "metric" in question.lower() or "benchmark" in question.lower() or "performance" in question.lower() or "empirical" in question.lower() or "finding" in question.lower():
        return "Evaluate Performance Benchmarks"
    if "challenge" in question.lower() or "security" in question.lower() or "trade-off" in question.lower() or "risk" in question.lower() or "limitation" in question.lower():
        return "Investigate Security & Trade-offs"
    if "implement" in question.lower() or "application" in question.lower() or "case study" in question.lower() or "real-world" in question.lower():
        return "Examine Practical Implementations"
    if "compare" in question.lower() or "alternative" in question.lower() or "compet" in question.lower() or "versus" in question.lower():
        return "Compare Alternative Solutions"
    if "future" in question.lower() or "trend" in question.lower() or "roadmap" in question.lower() or "recommend" in question.lower():
        return "Identify Future Trends & Standards"

    words = cleaned.split()
    if len(words) >= 3:
        title = " ".join(words[:5])
        return title[0].upper() + title[1:]
    return f"Investigate Step {idx + 1}"


def extract_json_from_text(text: str) -> dict:
    """Extracts and parses JSON object from model output."""
    clean_text = text.strip()
    if "```json" in clean_text:
        match = re.search(r"```json\s*(.*?)\s*```", clean_text, re.DOTALL)
        if match:
            clean_text = match.group(1).strip()
    elif "```" in clean_text:
        match = re.search(r"```\s*(.*?)\s*```", clean_text, re.DOTALL)
        if match:
            clean_text = match.group(1).strip()

    return json.loads(clean_text)


async def plan_research_node(state: AgentState, user_feedback: Optional[str] = None) -> AgentState:
    mode = (state.mode or "standard").lower()
    norm_mode = "quick" if mode == "quick" else ("indepth" if mode in ["indepth", "deep", "academic"] else "standard")
    
    logger.info(f"Running Planner Node with Groq for run_id: {state.run_id} (Mode: {norm_mode}, Feedback: {user_feedback})")
    state.current_stage = "planning"
    state.status = "PLANNING"

    provider = get_llm_provider()

    if norm_mode == "quick":
        mode_instruction = (
            "CRITICAL MODE REQUIREMENT: Quick Research Mode.\n"
            "- You MUST generate EXACTLY TWO (2) concise, high-impact subquestions.\n"
            "- Subquestion 1: Foundational overview, definitions, and core mechanisms.\n"
            "- Subquestion 2: Practical findings, performance benchmarks, and key takeaways.\n"
            "- Keep search queries focused and limited to 2 search queries per subquestion."
        )
    elif norm_mode == "indepth":
        mode_instruction = (
            "CRITICAL MODE REQUIREMENT: In-Depth Literature Review & Comprehensive Research Mode.\n"
            "- You MUST generate 4 to 6 thorough, multidimensional subquestions.\n"
            "- Subquestion 1: Theoretical & Architectural Foundations.\n"
            "- Subquestion 2: Empirical Performance Metrics & Quantitative Benchmarks.\n"
            "- Subquestion 3: Conflicting Findings, Contradictions, and Edge Cases.\n"
            "- Subquestion 4: Security Vulnerabilities, Risks, and Operational Trade-offs.\n"
            "- Subquestion 5: Practical Engineering Implementation & Industry Case Studies.\n"
            "- Subquestion 6: Research Gaps, Limitations, and Future Directions."
        )
    else:  # standard
        mode_instruction = (
            "CRITICAL MODE REQUIREMENT: Standard Research Mode.\n"
            "- You MUST generate 3 to 4 balanced subquestions breaking down the topic into logical research steps.\n"
            "- Subquestion 1: Core Concepts and Foundations.\n"
            "- Subquestion 2: Performance Evaluation & Metrics.\n"
            "- Subquestion 3: Security Risks, Limitations, and Trade-offs.\n"
            "- Subquestion 4: Practical Implementations & Recommendations."
        )

    system_prompt = (
        "You are the Research Planner Agent for ResAI, an evidence-driven autonomous AI research system powered by Groq.\n"
        "Your task is to analyze the user's research question, domain, and objective, and generate a structured research plan in valid JSON format.\n\n"
        f"{mode_instruction}\n\n"
        "The plan MUST be valid JSON with this structure:\n"
        "{\n"
        '  "main_question": "...",\n'
        '  "subquestions": [\n'
        '    {\n'
        '      "id": "sq_1",\n'
        '      "title": "3-5 word concise title",\n'
        '      "question": "Specific question to research",\n'
        '      "search_queries": ["search query 1", "search query 2"],\n'
        '      "evidence_required": "Type of evidence required",\n'
        '      "status": "PENDING"\n'
        "    }\n"
        "  ],\n"
        '  "relevant_source_types": ["web", "academic", "official"],\n'
        '  "analytical_approach": "...",\n'
        '  "verification_strategy": "...",\n'
        '  "completion_criteria": "..."\n'
        "}\n\n"
        "REQUIREMENTS:\n"
        "1. Each subquestion MUST have a short, meaningful 3-5 word 'title' (e.g. 'Understand Core Foundations', 'Evaluate Performance Benchmarks', 'Investigate Security & Trade-offs').\n"
        "2. Provide realistic search queries for each subquestion."
    )

    user_prompt = (
        f"Main Question: {state.question}\n"
        f"Objective: {state.objective or 'Comprehensive evidence synthesis'}\n"
        f"Domain: {state.domain}\n"
        f"Mode: {norm_mode}\n"
    )
    if user_feedback:
        user_prompt += (
            f"\nUser Feedback for Plan Revision: {user_feedback}\n"
            f"Generate an alternative plan respecting {norm_mode} mode exploring different technical perspectives and subquestion angles."
        )

    messages = [
        LLMMessage(role="system", content=system_prompt),
        LLMMessage(role="user", content=user_prompt),
    ]

    try:
        temp = 0.5 if user_feedback else 0.2
        response = await provider.generate_completion(messages, temperature=temp, json_mode=True)
        state.budget_tracker.tokens_used += response.tokens_used
        state.budget_tracker.estimated_cost_usd += response.estimated_cost_usd

        parsed_data = extract_json_from_text(response.content)

        raw_subqs = parsed_data.get("subquestions", [])
        if norm_mode == "quick" and len(raw_subqs) > 2:
            raw_subqs = raw_subqs[:2]

        subq_list = []
        for idx, sq in enumerate(raw_subqs):
            q_text = sq.get("question", "")
            title_text = sq.get("title") or generate_short_title(q_text, idx)
            queries = sq.get("search_queries") or [q_text or state.question]
            subq_list.append(
                SubQuestionSchema(
                    id=sq.get("id", f"sq_{idx+1}"),
                    title=title_text,
                    question=q_text,
                    search_queries=queries,
                    evidence_required=sq.get("evidence_required", "Verified source text"),
                    status="PENDING",
                )
            )

        if not subq_list:
            raise ValueError("Groq returned empty subquestions list.")

        plan = ResearchPlanSchema(
            main_question=parsed_data.get("main_question", state.question),
            subquestions=subq_list,
            relevant_source_types=parsed_data.get("relevant_source_types", ["web", "academic", "official"]),
            analytical_approach=parsed_data.get("analytical_approach", "Cross-source evidence synthesis"),
            verification_strategy=parsed_data.get("verification_strategy", "Primary documentation cross-reference"),
            completion_criteria=parsed_data.get("completion_criteria", "Subquestions resolved with verified citations"),
        )
        state.plan = plan
        state.status = "PENDING_APPROVAL"
        state.logs.append(f"Planner Agent generated {norm_mode} plan with {len(subq_list)} subquestions using Groq ({response.model_name}).")
        return state

    except Exception as e:
        logger.error(f"Planner node failed: {e}", exc_info=True)
        raise

