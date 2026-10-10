import pytest
from app.agents.state import AgentState
from app.agents.nodes.writer import report_writer_node
from app.services.export_service import export_service
from app.tools.citation_validator import execute_validate_citations


@pytest.mark.asyncio
async def test_report_quality_topic_autonomous_agents():
    topic_question = "What are the core technical foundations, benchmark performance, and security risks of Autonomous Research Assistants?"
    
    state = AgentState(
        run_id="test-topic-1",
        question=topic_question,
        objective="Comprehensive evaluation of autonomous research agents",
        domain="AI Systems",
        mode="deep",
        sources=[
            {
                "url": "https://arxiv.org/abs/2403.12345",
                "title": "Empirical Evaluation and Architectural Benchmarks for Autonomous Research Assistants",
                "domain": "arxiv.org",
                "publication_date": "2025-11-15",
                "content_text": "Autonomous research engines achieve 92.4% task completion rate with 380ms latency.",
            },
            {
                "url": "https://acm.org/doi/10.1145/3678900",
                "title": "Security Architecture and Threat Modeling in Autonomous Research Systems",
                "domain": "acm.org",
                "publication_date": "2026-01-20",
                "content_text": "Mitigating prompt injection and SSRF risks in multi-agent retrieval pipelines.",
            },
        ],
        evidence=[
            {
                "source_url": "https://arxiv.org/abs/2403.12345",
                "claim_text": "Multi-stage verification pipelines reach 92.4% task completion rate.",
                "supporting_text": "Evaluation across 500 multi-step research queries.",
                "evidence_type": "stat",
                "confidence_score": 0.96,
            }
        ]
    )

    final_state = await report_writer_node(state)
    report_md = final_state.markdown_report
    import re
    norm_md = re.sub(r"[\u2010\u2011\u2012\u2013\u2014]", "-", report_md)

    # 1. Verify 8-part structure
    assert "## Research Overview" in norm_md
    assert "## Key Findings" in norm_md
    assert "## Performance Metrics" in norm_md
    assert "## Security Risks and Trade-offs" in norm_md or "## Security Risks" in norm_md or "## Security" in norm_md
    assert "## Comparison" in norm_md
    assert "## Practical Implications" in norm_md
    assert "## Conclusion" in norm_md
    assert "## Sources" in norm_md

    # 2. Verify topic specificity & absence of generic filler
    assert "Reliable evidence confirms the key principles" not in report_md
    assert "offers valuable capabilities" not in report_md
    assert "duckduckgo.com" not in report_md

    # 3. Verify topic relevance & bold highlights
    assert "Autonomous Research Assistants" in report_md or "autonomous" in report_md.lower()
    assert "**" in report_md  # selective bolding present

    # 4. Verify citation validation
    audit = await execute_validate_citations({
        "markdown_text": report_md,
        "available_source_ids": ["https://arxiv.org/abs/2403.12345", "https://acm.org/doi/10.1145/3678900"],
    })
    assert audit.total_citations_found > 0
    assert audit.resolved_citations_count > 0

    # 5. Verify PDF & Markdown export formatting
    pdf_bytes = export_service.export_pdf("Autonomous Research Assistants", report_md)
    assert len(pdf_bytes) > 500
    assert pdf_bytes.startswith(b"%PDF")

    md_bytes = export_service.export_markdown(report_md)
    assert len(md_bytes) > 200


@pytest.mark.asyncio
async def test_report_quality_topic_rust_vs_go():
    topic_question = "How do Rust and Go concurrency models compare in memory safety, throughput, and developer productivity?"
    
    state = AgentState(
        run_id="test-topic-2",
        question=topic_question,
        objective="Comparative analysis of concurrency and memory safety",
        domain="Systems Programming",
        mode="deep",
        sources=[
            {
                "url": "https://arxiv.org/abs/2404.99881",
                "title": "Comparative Throughput and Memory Safety in Rust vs Go Concurrency Architectures",
                "domain": "arxiv.org",
                "publication_date": "2025-10-10",
                "content_text": "Empirical benchmarks show zero-cost ownership abstractions in Rust vs CSP goroutines in Go.",
            }
        ],
        evidence=[
            {
                "source_url": "https://arxiv.org/abs/2404.99881",
                "claim_text": "Rust guarantees compile-time memory safety without a garbage collection pause.",
                "supporting_text": "Empirical tests measure 0ms GC pause in Rust vs 0.8ms in Go.",
                "evidence_type": "fact",
                "confidence_score": 0.95,
            }
        ]
    )

    final_state = await report_writer_node(state)
    report_md = final_state.markdown_report
    import re
    norm_md = re.sub(r"[\u2010\u2011\u2012\u2013\u2014]", "-", report_md)

    # 1. Verify 8-part structure
    assert "## Research Overview" in norm_md
    assert "## Key Findings" in norm_md
    assert "## Performance Metrics" in norm_md
    assert "## Security Risks and Trade-offs" in norm_md or "## Security Risks" in norm_md or "## Security" in norm_md
    assert "## Comparison" in norm_md
    assert "## Practical Implications" in norm_md
    assert "## Conclusion" in norm_md
    assert "## Sources" in norm_md

    # 4. Verify comparison table in generated report
    assert "|" in report_md
    lines_with_pipes = [l for l in report_md.split("\n") if l.strip().startswith("|") and not l.strip().startswith("|-")]
    assert len(lines_with_pipes) >= 2

    # 5. Verify HTML and DOCX exports
    html_bytes = export_service.export_html("Rust vs Go Concurrency", report_md)
    assert len(html_bytes) > 500
    assert b"<table" in html_bytes or b"<!DOCTYPE html>" in html_bytes

    docx_bytes = export_service.export_docx("Rust vs Go Concurrency", report_md)
    assert len(docx_bytes) > 500


@pytest.mark.asyncio
async def test_absence_of_mock_llm_provider():
    """Validates that mock LLM provider is eliminated and unsupported provider raises honest error."""
    from app.providers.factory import get_llm_provider
    from app.core.exceptions import LLMProviderException

    with pytest.raises(LLMProviderException) as exc_info:
        get_llm_provider("mock")
    assert "Unsupported LLM provider 'mock'" in str(exc_info.value)

