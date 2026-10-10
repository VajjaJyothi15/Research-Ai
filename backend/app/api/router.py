from fastapi import APIRouter

from app.api.v1.evidence import router as evidence_router
from app.api.v1.health import router as health_router
from app.api.v1.library import router as library_router
from app.api.v1.plans import router as plans_router
from app.api.v1.reports import router as reports_router
from app.api.v1.research import router as research_router
from app.api.v1.tools_api import router as tools_router
from app.api.v1.uploads import router as uploads_router

api_router = APIRouter()

api_router.include_router(health_router, tags=["Health"])
api_router.include_router(research_router, prefix="/research", tags=["Research"])
api_router.include_router(plans_router, tags=["Plans"])
api_router.include_router(evidence_router, tags=["Evidence"])
api_router.include_router(reports_router, tags=["Reports"])
api_router.include_router(uploads_router, prefix="/uploads", tags=["Uploads"])
api_router.include_router(tools_router, prefix="/tools", tags=["Tools"])
api_router.include_router(library_router, prefix="/library", tags=["Source Library"])
