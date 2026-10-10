import json
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_sse_live_progress_events():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Create a research run
        create_res = await ac.post(
            "/api/v1/research",
            json={
                "question": "What are the latest developments in quantum error correction for 2026?",
                "mode": "iterative",
                "depth": "standard",
            },
        )
        assert create_res.status_code == 201
        run_id = create_res.json()["id"]

        # 2. Check SSE stream before execution (planning stage replay)
        async with ac.stream("GET", f"/api/v1/research/{run_id}/events") as sse_stream:
            assert sse_stream.status_code == 200
            events_received = []
            async for line in sse_stream.aiter_lines():
                if line.startswith("data:"):
                    events_received.append(json.loads(line[5:].strip()))
                    break
            assert len(events_received) > 0
            assert events_received[0]["stage"] == "PLANNING"

        # 3. Approve and execute plan
        approve_res = await ac.post(f"/api/v1/research/{run_id}/plan/approve")
        assert approve_res.status_code == 200
        assert approve_res.json()["status"] in ["COMPLETED", "PARTIAL"]

        # 4. Check SSE stream after execution (all completed stages replayed)
        async with ac.stream("GET", f"/api/v1/research/{run_id}/events") as sse_stream_after:
            assert sse_stream_after.status_code == 200
            stages_seen = set()
            async for line in sse_stream_after.aiter_lines():
                if line.startswith("data:"):
                    data = json.loads(line[5:].strip())
                    stages_seen.add(data["stage"])
                    if data["status"] == "completed" and data["progress_percent"] == 100:
                        break
            assert "SEARCHING" in stages_seen
            assert "EXTRACTING" in stages_seen
            assert "VERIFYING" in stages_seen
            assert "ANALYZING" in stages_seen
            assert "WRITING" in stages_seen
            assert "COMPLETED" in stages_seen
