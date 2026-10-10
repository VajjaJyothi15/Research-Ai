import re
from app.agents.state import AgentState
from app.core.logging import logger
from app.providers.base import LLMMessage
from app.providers.factory import get_llm_provider


async def report_writer_node(state: AgentState) -> AgentState:
    mode = (state.mode or "standard").lower()
    norm_mode = "quick" if mode == "quick" else ("indepth" if mode in ["indepth", "deep", "academic"] else "standard")
    
    logger.info(f"Running Report Writer Node with Groq for run_id: {state.run_id} (Mode: {norm_mode})")
    state.current_stage = "writing"
    state.status = "WRITING"

    provider = get_llm_provider()

    sources_summary = []
    for idx, s in enumerate(state.sources, 1):
        snippet = (s.get("content_text") or "")[:600]
        pub_date = s.get("publication_date") or "2026"
        author = s.get("author") or s.get("domain") or "Web Source"
        sources_summary.append(
            f"[{idx}] Title: {s.get('title')}\n"
            f"    URL: {s.get('url')}\n"
            f"    Author/Publisher: {author}\n"
            f"    Date: {pub_date}\n"
            f"    Domain: {s.get('domain') or 'web'}\n"
            f"    Excerpt: {snippet}"
        )
    sources_text = "\n\n".join(sources_summary) if sources_summary else "No external sources retrieved."

    evidence_summary = []
    for idx, e in enumerate(state.evidence, 1):
        evidence_summary.append(
            f"Evidence {idx}: Claim='{e.get('claim_text')}', SupportingExcerpt='{e.get('supporting_text')}', SourceURL='{e.get('source_url')}'"
        )
    evidence_text = "\n".join(evidence_summary) if evidence_summary else "No verified evidence items recorded."

    contradictions_summary = []
    for idx, c in enumerate(state.contradictions, 1):
        contradictions_summary.append(
            f"Contradiction {idx}: Topic='{c.get('topic')}', Claim A='{c.get('claim_a')}', Claim B='{c.get('claim_b')}', Description='{c.get('description')}'"
        )
    contradictions_text = "\n".join(contradictions_summary) if contradictions_summary else "No direct cross-source contradictions identified."

    matrix_data = state.analysis_results.get("comparison_matrix", {}) if state.analysis_results else {}
    matrix_text = ""
    if matrix_data and matrix_data.get("rows"):
        matrix_text = f"Synthesized Comparison Matrix Data:\nHeaders: {matrix_data.get('headers')}\nRows: {matrix_data.get('rows')}"

    # Construct mode-specific guidelines
    if norm_mode == "quick":
        structure_instructions = (
            "MODE SPECIFICATION: QUICK RESEARCH REPORT (Fast, high-level overview)\n"
            "Produce a concise, high-impact report with these exact sections:\n"
            "# [Engaging, Topic-Specific Report Title]\n\n"
            "## Research Overview\n"
            "Provide a crisp 1-2 paragraph introduction summarizing the core question and main takeaways.\n\n"
            "## Key Findings\n"
            "Detail 2-3 essential, evidence-backed findings. Use **bold highlights** and cite sources [1], [2].\n\n"
            "## Comparison\n"
            "Include a concise Markdown comparison table comparing key approaches with citations.\n"
            "Format: `| Solution / Approach | Key Mechanism | Performance / Metric | Supporting Source |`\n\n"
            "## Practical Implications & Takeaways\n"
            "Summarize the most important engineering and operational takeaways in 1-2 paragraphs or bullet points.\n\n"
            "## Sources\n"
            "List every cited source as:\n"
            "- [1] [Source Title](Source URL) - Author/Publisher (Publication Date) - Domain / Excerpt\n"
        )
    elif norm_mode == "indepth":
        structure_instructions = (
            "MODE SPECIFICATION: IN-DEPTH COMPREHENSIVE LITERATURE REVIEW & EMPIRICAL REPORT\n"
            "Produce an evidence-backed report with all of these mandatory sections:\n"
            "# [Engaging, Topic-Specific Report Title]\n\n"
            "## Research Overview\n"
            "Explain theoretical foundations, background, architecture, and problem formulation in 1-2 dense paragraphs.\n\n"
            "## Key Findings\n"
            "Analyze key multi-perspective findings with evidence synthesis. Ground points in citations [1], [2].\n\n"
            "## Performance Metrics\n"
            "Present measurable benchmarks, throughput, latency, accuracy, or efficiency metrics from evidence.\n\n"
            "## Security Risks and Trade-offs\n"
            "Analysis of attack vectors, security trade-offs, and safeguards.\n\n"
            "## Comparison\n"
            "Include a Markdown comparison table.\n"
            "Format: `| Architecture / Method | Core Strengths | Performance & Latency | Security & Limitations | Supporting Source |`\n\n"
            "## Conflicting Findings and Research Gaps\n"
            "Evaluate contradictions, limitations, and future directions.\n\n"
            "## Practical Implications\n"
            "Actionable deployment guidelines and production considerations.\n\n"
            "## Conclusion\n"
            "Synthesize strategic takeaways and outlook in 1 focused paragraph.\n\n"
            "## Sources\n"
            "List all retrieved primary sources with complete metadata:\n"
            "- [1] [Source Title](Source URL) - Author/Publisher (Publication Date) - Domain / Excerpt\n"
        )
    else:  # standard
        structure_instructions = (
            "MODE SPECIFICATION: STANDARD BALANCED RESEARCH REPORT\n"
            "Produce a structured, evidence-backed report with all of these mandatory sections:\n"
            "# [Engaging, Topic-Specific Report Title]\n\n"
            "## Research Overview\n"
            "Explain research question and technical context in 1-2 focused paragraphs.\n\n"
            "## Key Findings\n"
            "Detail major findings grounded in evidence citations [1], [2].\n\n"
            "## Performance Metrics\n"
            "Present measurable benchmarks, empirical results, and efficiency metrics.\n\n"
            "## Security Risks and Trade-offs\n"
            "Analyze security considerations and operational constraints.\n\n"
            "## Comparison\n"
            "Include a Markdown comparison table with evidence citations.\n"
            "Format: `| Approach / Model | Key Feature | Benchmark Metric | Trade-off | Supporting Source |`\n\n"
            "## Practical Implications\n"
            "Provide concrete engineering recommendations.\n\n"
            "## Conclusion\n"
            "Summarize takeaways in 1 concise paragraph.\n\n"
            "## Sources\n"
            "Provide complete numbered reference list:\n"
            "- [1] [Source Title](Source URL) - Author/Publisher (Publication Date) - Domain / Excerpt\n"
        )

    system_prompt = (
        f"You are the Principal Research Report Writer Agent for ResAI, an autonomous evidence-driven research platform powered by Groq.\n"
        f"Your mission is to author an authoritative, insightful, and completely evidence-grounded technical research report.\n\n"
        f"{structure_instructions}\n\n"
        "CRITICAL CITATION AND EVIDENCE RULES:\n"
        "1. Every factual statement or comparison must be traceable to the retrieved sources via numbered citations [1], [2], [3].\n"
        "2. The numbering [1], [2], ... in the text MUST match the corresponding entry in the ## Sources list.\n"
        "3. Preserve actual source URLs and DOIs. NEVER invent fake URLs, placeholder links, or fabricated papers.\n"
        "4. If no external sources were retrieved or data is absent, state the limitation honestly without pretending evidence was verified.\n"
        "5. Avoid generic filler words ('In today's fast-paced world...'). Write with crisp technical clarity."
    )

    user_prompt = (
        f"Research Question: {state.question}\n"
        f"Objective: {state.objective or 'Comprehensive evidence synthesis'}\n"
        f"Domain: {state.domain}\n"
        f"Mode: {norm_mode}\n\n"
        f"Retrieved Genuine Sources (use these for numbered citations [1], [2], ...):\n{sources_text}\n\n"
        f"Verified Evidence Claims:\n{evidence_text}\n\n"
        f"Identified Contradictions & Nuances:\n{contradictions_text}\n\n"
        f"{matrix_text}"
    )

    messages = [
        LLMMessage(role="system", content=system_prompt),
        LLMMessage(role="user", content=user_prompt),
    ]

    try:
        response = await provider.generate_completion(messages, temperature=0.2)
        state.budget_tracker.tokens_used += response.tokens_used
        state.budget_tracker.estimated_cost_usd += response.estimated_cost_usd

        # Normalize any numerical prefixes in section headings (e.g. '## 1. Research Overview' -> '## Research Overview')
        content = response.content
        content = re.sub(r'(?m)^##\s*\d+[\.\)]\s*', '## ', content)

        state.markdown_report = content
        state.logs.append(f"Report Writer Agent generated {norm_mode} report with Groq ({response.model_name}).")
        return state
    except Exception as e:
        logger.error(f"Report writer failed with Groq: {e}", exc_info=True)
        raise


