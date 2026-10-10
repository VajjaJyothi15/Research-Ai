from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class ResAIException(HTTPException):
    def __init__(self, status_code: int, detail: str, code: str = "GENERIC_ERROR", extra: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=status_code, detail=detail)
        self.code = code
        self.extra = extra or {}


class ResourceNotFoundException(ResAIException):
    def __init__(self, resource_name: str, resource_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource_name} with ID '{resource_id}' not found.",
            code="RESOURCE_NOT_FOUND",
        )


class BudgetExceededException(ResAIException):
    def __init__(self, limit_type: str, max_limit: int, current_val: int):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Research run budget limit exceeded for '{limit_type}'. Limit: {max_limit}, Current: {current_val}.",
            code="BUDGET_EXCEEDED",
        )


class SSRFProtectionException(ResAIException):
    def __init__(self, target_url: str, reason: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"URL request blocked by security policy for '{target_url}': {reason}",
            code="SSRF_BLOCKED",
        )


class LLMProviderException(ResAIException):
    def __init__(self, provider: str, detail: str):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LLM Provider '{provider}' failed: {detail}",
            code="LLM_PROVIDER_ERROR",
        )
