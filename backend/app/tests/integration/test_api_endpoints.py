import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_health_check_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "llm_provider" in data


@pytest.mark.asyncio
async def test_full_research_creation_and_approval_flow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Create Research Run
        create_res = await ac.post("/api/v1/research", json={
            "question": "What are the core technical foundations and performance metrics of ResAI?",
            "objective": "Evaluate autonomous research performance",
            "domain": "AI Systems",
            "mode": "quick",
        })
        assert create_res.status_code == 201
        run_data = create_res.json()
        run_id = run_data["id"]
        assert run_data["status"] == "PENDING_APPROVAL"

        # 2. Get Plan
        plan_res = await ac.get(f"/api/v1/research/{run_id}/plan")
        assert plan_res.status_code == 200
        plan_data = plan_res.json()
        assert plan_data["run_id"] == run_id
        assert len(plan_data["subquestions_json"]) > 0

        # 3. Approve & Execute Plan
        approve_res = await ac.post(f"/api/v1/research/{run_id}/plan/approve")
        assert approve_res.status_code == 200
        executed_run = approve_res.json()
        assert executed_run["status"] in ["COMPLETED", "PARTIAL"]

        # 4. Get Report
        report_res = await ac.get(f"/api/v1/research/{run_id}/report")
        assert report_res.status_code == 200
        report = report_res.json()
        assert report["full_markdown"].startswith("# ") or "## " in report["full_markdown"]
        assert len(report["executive_summary"]) > 0

        # 5. Export Report (PDF, Markdown & HTML)
        report_id = report["id"]
        export_md = await ac.get(f"/api/v1/reports/{report_id}/export?format=md")
        assert export_md.status_code == 200
        assert "Content-Disposition" in export_md.headers

        export_html = await ac.get(f"/api/v1/reports/{report_id}/export?format=html")
        assert export_html.status_code == 200
        assert "text/html" in export_html.headers["content-type"]

        export_pdf = await ac.get(f"/api/v1/reports/{report_id}/export?format=pdf")
        assert export_pdf.status_code == 200
        assert export_pdf.headers["content-type"] == "application/pdf"

