import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.db.session import async_engine, AsyncSessionLocal
from app.db.base import Base
from app.db.models.models import ResearchRun, ResearchPlan, Source, EvidenceItem, Report, ReportVersion


async def seed_demo_data():
    print("Initializing database tables...")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        print("Seeding ResAI demo research run...")
        run = ResearchRun(
            question="What are the comparative performance metrics and security trade-offs of autonomous agent frameworks?",
            objective="Evaluate enterprise suitability and citation fidelity",
            domain="AI Systems",
            mode="deep",
            status="COMPLETED",
            current_stage="completed",
        )
        session.add(run)
        await session.flush()

        plan = ResearchPlan(
            run_id=run.id,
            version=1,
            status="APPROVED",
            main_question=run.question,
            subquestions_json=[
                {"id": "sq_1", "question": "What are the core technical foundations?", "search_queries": ["agent framework architecture"], "evidence_required": "Documentation", "status": "RESOLVED"},
                {"id": "sq_2", "question": "What are empirical benchmark stats?", "search_queries": ["agent benchmarks citation accuracy"], "evidence_required": "Empirical data", "status": "RESOLVED"},
            ],
            plan_data_json={"analytical_approach": "Cross-source evidence graph"},
        )
        session.add(plan)

        src = Source(
            run_id=run.id,
            url="https://resai.dev/docs/spec",
            canonical_url="https://resai.dev/docs/spec",
            title="ResAI Autonomous Agent Technical Specification & Benchmarks",
            author="ResAI Architecture Team",
            publication_date="2026-01-15",
            source_type="official",
            domain="resai.dev",
            content_text="ResAI framework provides claim-level evidence grounding, 100% citation audit resolution, and bounded stateful workflows.",
        )
        session.add(src)
        await session.flush()

        ev = EvidenceItem(
            run_id=run.id,
            source_id=src.id,
            claim_text="Automated citation auditing guarantees 100% resolution between report references and stored sources.",
            supporting_text="Citation auditing passes verify each report reference against database stored evidence records.",
            publication_date="2026-01-15",
            evidence_type="stat",
            confidence_score=0.98,
            verification_status="VERIFIED",
            relationship="SUPPORTING",
        )
        session.add(ev)

        report = Report(
            run_id=run.id,
            title="Research Report: Autonomous Agent Frameworks",
            executive_summary="Empirical evaluation confirms that structured evidence graphs reduce hallucinated citations while preserving verifiable claim provenance [1].",
            full_markdown="""# Research Report: Autonomous Agent Frameworks

## Executive Summary
This research report provides an evidence-driven evaluation of autonomous research assistant architectures [1].

## Key Findings
1. Autonomous tool calling ensures factual evidence grounding for complex research queries [1].
2. Cross-source contradiction analysis identifies discrepancies in reported benchmark performance [1].
3. Citation auditing guarantees 100% resolution between in-text citations and verified sources [1].

## References
- [1] ResAI Autonomous Agent Technical Specification & Benchmarks (2026). https://resai.dev/docs/spec
""",
        )
        session.add(report)

        await session.commit()
        print(f"Successfully seeded demo research run with ID: {run.id}")


if __name__ == "__main__":
    asyncio.run(seed_demo_data())
