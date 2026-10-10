import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.agents.nodes.planner import plan_research_node
from app.agents.state import AgentState
from app.providers.gemini import GeminiProvider
from app.providers.openai import OpenAIProvider
from app.core.exceptions import LLMProviderException


@pytest.mark.asyncio
async def test_create_research_plan_success():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Test creating plan with valid question
        res = await ac.post("/api/v1/research", json={
            "question": "What are the latest architectures and performance benchmarks in quantum machine learning?",
            "objective": "Evaluate practical quantum ML deployment",
            "domain": "technology",
            "mode": "deep",
        })
        assert res.status_code == 201
        data = res.json()
        assert data["id"] is not None
        assert data["status"] == "PENDING_APPROVAL"
        assert data["question"] == "What are the latest architectures and performance benchmarks in quantum machine learning?"

        # Verify plan was created in DB
        run_id = data["id"]
        plan_res = await ac.get(f"/api/v1/research/{run_id}/plan")
        assert plan_res.status_code == 200
        plan_data = plan_res.json()
        assert plan_data["run_id"] == run_id
        assert len(plan_data["subquestions_json"]) >= 2

        # Check that steps have short readable titles
        for sq in plan_data["subquestions_json"]:
            assert "title" in sq
            assert len(sq["title"]) > 0


@pytest.mark.asyncio
async def test_create_research_plan_validation_empty_or_short_question():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Test empty question
        res_empty = await ac.post("/api/v1/research", json={
            "question": "",
            "mode": "deep",
        })
        assert res_empty.status_code == 422
        err_empty = res_empty.json()
        assert "error" in err_empty or "detail" in err_empty

        # Test short question (< 5 chars)
        res_short = await ac.post("/api/v1/research", json={
            "question": "Why?",
            "mode": "deep",
        })
        assert res_short.status_code == 422
        err_short = res_short.json()
        assert "at least 5 characters" in err_short.get("detail", "") or "error" in err_short


@pytest.mark.asyncio
async def test_create_plan_different_modes_and_regeneration():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create quick mode plan
        res_quick = await ac.post("/api/v1/research", json={
            "question": "How do Vector Databases compare against Graph Databases for RAG retrieval?",
            "domain": "technology",
            "mode": "quick",
        })
        assert res_quick.status_code == 201
        run_id = res_quick.json()["id"]

        # Regenerate plan ("Try another plan")
        regen_res = await ac.post(f"/api/v1/research/{run_id}/plan/regenerate", json={
            "user_feedback": "Focus more on enterprise scalability and latency trade-offs",
        })
        assert regen_res.status_code == 200
        regen_data = regen_res.json()
        assert regen_data["version"] >= 2
        assert len(regen_data["subquestions_json"]) >= 2


@pytest.mark.asyncio
async def test_unconfigured_provider_error_handling():
    # Test that GeminiProvider raises clear exception when API key is missing
    provider = GeminiProvider(api_key="")
    with pytest.raises(LLMProviderException) as exc_info:
        await provider.generate_completion(messages=[])
    assert "GEMINI_API_KEY" in str(exc_info.value)

    # Test that GroqProvider raises clear exception when API key is missing
    from app.providers.groq import GroqProvider
    provider_groq = GroqProvider(api_key="")
    with pytest.raises(LLMProviderException) as exc_info_gr:
        await provider_groq.generate_completion(messages=[])
    assert "GROQ_API_KEY" in str(exc_info_gr.value)

    # Test that OpenAIProvider raises clear exception when API key is missing
    provider_openai = OpenAIProvider(api_key="")
    with pytest.raises(LLMProviderException) as exc_info_oa:
        await provider_openai.generate_completion(messages=[])
    assert "OPENAI_API_KEY" in str(exc_info_oa.value)

