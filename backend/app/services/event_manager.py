import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from app.core.logging import logger

STAGE_CONFIG = {
    "PLANNING": {"index": 1, "label": "Research planning", "default_pct": 15},
    "SEARCHING": {"index": 2, "label": "Web and academic search", "default_pct": 30},
    "EXTRACTING": {"index": 3, "label": "Evidence extraction", "default_pct": 45},
    "VERIFYING": {"index": 4, "label": "Cross-source verification", "default_pct": 60},
    "ANALYZING": {"index": 5, "label": "Comparison and analysis", "default_pct": 75},
    "WRITING": {"index": 6, "label": "Report generation", "default_pct": 90},
    "CITATION_AUDIT": {"index": 6, "label": "Citation audit", "default_pct": 95},
    "COMPLETED": {"index": 7, "label": "Completed", "default_pct": 100},
    "FAILED": {"index": 0, "label": "Execution failed", "default_pct": 0},
    "CANCELLED": {"index": 0, "label": "Cancelled", "default_pct": 0},
}


class ResearchEventManager:
    """Manages real-time event distribution and historical replay for research runs."""

    def __init__(self):
        self._history: Dict[str, List[Dict[str, Any]]] = {}
        self._subscribers: Dict[str, Set[asyncio.Queue]] = {}

    def emit_event(
        self,
        research_id: str,
        stage: str,
        message: str,
        progress_percent: Optional[int] = None,
        status: str = "running",
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Emits a real execution event to all active SSE subscribers and appends to run history."""
        cfg = STAGE_CONFIG.get(stage.upper(), {"index": 1, "label": stage, "default_pct": 10})
        pct = progress_percent if progress_percent is not None else cfg["default_pct"]

        # Ensure 100% is only reported when truly completed
        if status != "completed" and pct >= 100:
            pct = 95

        event = {
            "research_id": research_id,
            "stage": stage.upper(),
            "stage_label": cfg["label"],
            "stage_index": cfg["index"],
            "total_stages": 7,
            "progress_percent": pct,
            "message": message,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": details or {},
        }

        if research_id not in self._history:
            self._history[research_id] = []
        self._history[research_id].append(event)

        logger.info(f"[SSE Event] run={research_id} stage={stage} status={status} pct={pct}% msg='{message}'")

        # Broadcast to active queues
        if research_id in self._subscribers:
            for q in list(self._subscribers[research_id]):
                try:
                    q.put_nowait(event)
                except Exception as e:
                    logger.warning(f"Error putting event to subscriber queue for {research_id}: {e}")

        return event

    def get_history(self, research_id: str) -> List[Dict[str, Any]]:
        """Returns the complete sequence of events recorded for a research run."""
        return list(self._history.get(research_id, []))

    def subscribe(self, research_id: str) -> asyncio.Queue:
        """Subscribes an SSE client to receive live events for a research run."""
        q = asyncio.Queue()
        if research_id not in self._subscribers:
            self._subscribers[research_id] = set()
        self._subscribers[research_id].add(q)
        return q

    def unsubscribe(self, research_id: str, q: asyncio.Queue):
        """Unsubscribes an SSE client when connection terminates."""
        if research_id in self._subscribers:
            self._subscribers[research_id].discard(q)
            if not self._subscribers[research_id]:
                del self._subscribers[research_id]

    def clear(self, research_id: str):
        """Clears cached history for a research run."""
        if research_id in self._history:
            del self._history[research_id]


event_manager = ResearchEventManager()
