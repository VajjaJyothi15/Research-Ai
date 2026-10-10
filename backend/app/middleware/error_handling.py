from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.core.exceptions import ResAIException
from app.core.logging import logger


async def resai_exception_handler(request: Request, exc: ResAIException):
    logger.error(f"Handled ResAI Exception [{exc.code}]: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.detail,
                "extra": exc.extra,
            },
            "detail": exc.detail,
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    messages = []
    for err in errors:
        field = " -> ".join([str(loc) for loc in err.get("loc", []) if loc != "body"])
        msg = err.get("msg", "Invalid value")
        if "string_too_short" in err.get("type", ""):
            msg = "Research question must be at least 5 characters long."
        messages.append(f"{field}: {msg}" if field else msg)
    combined_msg = "; ".join(messages) if messages else "Invalid request parameters provided."
    logger.warning(f"Validation Error: {combined_msg}")
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": combined_msg,
                "extra": errors,
            },
            "detail": combined_msg,
        },
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTP Exception [{exc.status_code}]: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": str(exc.detail),
            },
            "detail": str(exc.detail),
        },
    )


async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception: {exc}", exc_info=True)
    msg = str(exc) if str(exc) else "An unexpected error occurred. Please try again later."
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": msg,
            },
            "detail": msg,
        },
    )
