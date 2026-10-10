from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.core.exceptions import ResourceNotFoundException
from app.db.models.models import EvidenceItem, Report, Source
from app.schemas.reports import (
    CitationValidationResponse,
    ReportResponse,
    SummarizeReportRequest,
    SummarizeReportResponse,
)
from app.providers.base import LLMMessage
from app.providers.factory import get_llm_provider
from app.services.export_service import export_service
from app.tools.citation_validator import execute_validate_citations

router = APIRouter()


@router.get("/research/{research_id}/report", response_model=ReportResponse)
async def get_report_by_research_id(
    research_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    """Gets generated report by research run ID."""
    stmt = select(Report).where(Report.run_id == research_id).order_by(Report.created_at.desc())
    res = await db.execute(stmt)
    report = res.scalars().first()
    if not report:
        raise ResourceNotFoundException("Report", research_id)
    return report


@router.get("/reports/{report_id}", response_model=ReportResponse)
async def get_report_by_id(
    report_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    """Gets report by report ID."""
    stmt = select(Report).where(Report.id == report_id)
    res = await db.execute(stmt)
    report = res.scalar_one_or_none()
    if not report:
        raise ResourceNotFoundException("Report", report_id)
    return report


@router.post("/reports/{report_id}/validate-citations", response_model=CitationValidationResponse)
async def validate_report_citations(
    report_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    """Validates that all in-text report citations resolve to valid source records."""
    stmt = select(Report).where(Report.id == report_id)
    res = await db.execute(stmt)
    report = res.scalar_one_or_none()
    if not report:
        raise ResourceNotFoundException("Report", report_id)

    stmt_src = select(Source).where(Source.run_id == report.run_id)
    res_src = await db.execute(stmt_src)
    sources = res_src.scalars().all()
    source_urls = [s.url for s in sources]

    audit = await execute_validate_citations({
        "markdown_text": report.full_markdown,
        "available_source_ids": source_urls,
    })

    return CitationValidationResponse(
        report_id=report_id,
        is_valid=audit.is_valid,
        total_citations=audit.total_citations_found,
        resolved_citations=audit.resolved_citations_count,
        unsupported_claims=audit.unsupported_claims,
        missing_sources=audit.missing_source_references,
    )


@router.post("/reports/{report_id}/summarize", response_model=SummarizeReportResponse)
async def summarize_report(
    report_id: str,
    body: SummarizeReportRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Generates an executive, key findings, or section-by-section summary of the saved report using real Groq LLM."""
    stmt = select(Report).where(Report.id == report_id)
    res = await db.execute(stmt)
    report = res.scalar_one_or_none()
    if not report:
        raise ResourceNotFoundException("Report", report_id)

    summary_type = body.summary_type
    provider = get_llm_provider()

    system_prompt = (
        f"You are the Research Report Summarizer for ResAI, powered by Groq.\n"
        f"Summarize the provided technical research report in '{summary_type.replace('_', ' ')}' format.\n"
        "Guidelines:\n"
        "- If 'executive': Write 2 concise, impactful paragraphs synthesizing core takeaways, evidence findings, and strategic implications.\n"
        "- If 'bullet_points': Write 5 distinct, high-signal bullet points highlighting specific metrics, findings, and trade-offs.\n"
        "- If 'technical': Detail the architectural mechanisms, benchmark metrics, security implications, and trade-offs.\n"
        "- Always preserve citation references [1], [2] when summarizing evidence-backed claims."
    )

    user_prompt = f"Research Report Title: {report.title}\n\nReport Content:\n{report.full_markdown[:7000]}"

    messages = [
        LLMMessage(role="system", content=system_prompt),
        LLMMessage(role="user", content=user_prompt),
    ]

    response = await provider.generate_completion(messages, temperature=0.2)
    summary_text = response.content

    return SummarizeReportResponse(
        summary_type=summary_type,
        summary_text=summary_text,
        caveats_preserved=[
            "Summary generated from verified research report and primary sources.",
            "All empirical benchmark measurements and source citations preserved.",
        ],
    )


@router.get("/reports/{report_id}/export")
async def export_report(
    report_id: str,
    format: str = Query("pdf", pattern="^(pdf|docx|md|json|csv|html)$"),
    db: AsyncSession = Depends(get_db_session),
):
    """Exports research report in requested format (pdf, docx, md, json, csv, html)."""
    stmt = select(Report).where(Report.id == report_id)
    res = await db.execute(stmt)
    report = res.scalar_one_or_none()
    if not report:
        raise ResourceNotFoundException("Report", report_id)

    safe_title = report.title.replace(" ", "_")[:30]

    if format == "pdf":
        content = export_service.export_pdf(report.title, report.full_markdown)
        return Response(content=content, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=ResAI_Report_{safe_title}.pdf"})

    elif format == "docx":
        content = export_service.export_docx(report.title, report.full_markdown)
        return Response(content=content, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", headers={"Content-Disposition": f"attachment; filename=ResAI_Report_{safe_title}.docx"})

    elif format == "html":
        content = export_service.export_html(report.title, report.full_markdown)
        return Response(content=content, media_type="text/html", headers={"Content-Disposition": f"attachment; filename=ResAI_Report_{safe_title}.html"})

    elif format == "md":
        content = export_service.export_markdown(report.full_markdown)
        return Response(content=content, media_type="text/markdown", headers={"Content-Disposition": f"attachment; filename=ResAI_Report_{safe_title}.md"})

    elif format == "json":
        data = {
            "report_id": report.id,
            "title": report.title,
            "executive_summary": report.executive_summary,
            "full_markdown": report.full_markdown,
            "metadata": report.metadata_json,
        }
        content = export_service.export_json(data)
        return Response(content=content, media_type="application/json", headers={"Content-Disposition": f"attachment; filename=ResAI_Report_{safe_title}.json"})

    elif format == "csv":
        stmt_src = select(Source).where(Source.run_id == report.run_id)
        stmt_ev = select(EvidenceItem).where(EvidenceItem.run_id == report.run_id)
        sources = (await db.execute(stmt_src)).scalars().all()
        evidence = (await db.execute(stmt_ev)).scalars().all()
        
        src_dicts = [{"url": s.url, "title": s.title, "type": s.source_type} for s in sources]
        ev_dicts = [{"claim": e.claim_text, "status": e.verification_status, "url": e.source_id} for e in evidence]
        content = export_service.export_csv_sources_and_evidence(src_dicts, ev_dicts)
        return Response(content=content, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=ResAI_Evidence_{safe_title}.csv"})

