from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import ResAIException
from app.core.logging import logger
from app.db.base import Base
from app.db.session import async_engine
from app.middleware.error_handling import generic_exception_handler, resai_exception_handler
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing ResAI Backend Application...")
    # Initialize DB tables for zero-config local dev/tests
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    logger.info("Shutting down ResAI Backend Application...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    lifespan=lifespan,
)

# Configure Middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN, "http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:4173", "http://127.0.0.1:4173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException
from app.middleware.error_handling import (
    generic_exception_handler,
    http_exception_handler,
    resai_exception_handler,
    validation_exception_handler,
)

# Exception Handlers
app.add_exception_handler(ResAIException, resai_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Include Routers
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    return {
        "message": "Welcome to ResAI — An Evidence-Driven Autonomous Research Assistant API",
        "documentation": f"{settings.API_V1_STR}/docs",
        "version": settings.VERSION,
    }
