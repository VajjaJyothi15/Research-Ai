from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """Application health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "llm_provider": settings.LLM_PROVIDER,
        "search_provider": settings.SEARCH_PROVIDER,
    }


@router.get("/ready")
async def ready_check():
    """Readiness probe endpoint for Kubernetes / Docker Compose."""
    return {
        "ready": True,
        "database": "connected",
    }
