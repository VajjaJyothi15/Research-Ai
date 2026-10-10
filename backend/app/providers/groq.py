import asyncio
import json
import re
from typing import Any, Dict, List, Optional
import httpx
from app.core.config import settings
from app.core.exceptions import LLMProviderException
from app.core.logging import logger
from app.providers.base import BaseLLMProvider, LLMMessage, LLMResponse

try:
    from groq import AsyncGroq, APIError, RateLimitError
    HAS_GROQ_SDK = True
except ImportError:
    HAS_GROQ_SDK = False


class GroqProvider(BaseLLMProvider):
    """Real Groq LLM Provider implementation with official SDK and HTTP fallback,
    supporting high-speed inference with automatic fallback across available models.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key if api_key is not None else settings.GROQ_API_KEY
        self.model_name = model_name or settings.GROQ_MODEL or "openai/gpt-oss-20b"
        self._client: Optional[Any] = None
        if HAS_GROQ_SDK and self.api_key:
            self._client = AsyncGroq(api_key=self.api_key, timeout=15.0, max_retries=0)

    async def generate_completion(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.2,
        tools: Optional[List[Dict[str, Any]]] = None,
        json_mode: bool = False,
    ) -> LLMResponse:
        if not self.api_key:
            raise LLMProviderException(
                "groq",
                "Groq API key is not configured. Please set the GROQ_API_KEY environment variable in your .env file."
            )

        # Retry configuration - fast failover to avoid test/workflow stalls
        max_retries = 1
        backoff = 0.5

        # Fallback list of models available on Groq
        models_to_try = [self.model_name]
        for alt in [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "openai/gpt-oss-20b",
            "openai/gpt-oss-120b",
            "qwen/qwen3.8-27b",
        ]:
            if alt not in models_to_try:
                models_to_try.append(alt)

        last_error = None
        for current_model in models_to_try:
            for attempt in range(max_retries):
                use_strict_json = json_mode and (attempt == 0)
                try:
                    if self._client:
                        # Use official Groq Async client
                        formatted_messages = [{"role": m.role, "content": m.content} for m in messages]
                        kwargs: Dict[str, Any] = {
                            "model": current_model,
                            "messages": formatted_messages,
                            "temperature": temperature,
                        }
                        if "qwen" in current_model.lower():
                            kwargs["max_tokens"] = 950
                        if use_strict_json:
                            kwargs["response_format"] = {"type": "json_object"}
                        if tools:
                            kwargs["tools"] = tools

                        completion = await asyncio.wait_for(
                            self._client.chat.completions.create(**kwargs),
                            timeout=20.0
                        )
                        choice = completion.choices[0].message
                        content = choice.content or ""
                        tool_calls = getattr(choice, "tool_calls", None)
                        tokens = completion.usage.total_tokens if completion.usage else 0

                        return LLMResponse(
                            content=content,
                            tool_calls=tool_calls,
                            model_name=current_model,
                            tokens_used=tokens,
                            estimated_cost_usd=(tokens / 1000) * 0.0005,
                        )

                    else:
                        # Use direct HTTP request to Groq OpenAI-compatible endpoint
                        url = "https://api.groq.com/openai/v1/chat/completions"
                        headers = {
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json",
                        }
                        formatted_messages = [{"role": m.role, "content": m.content} for m in messages]
                        payload: Dict[str, Any] = {
                            "model": current_model,
                            "messages": formatted_messages,
                            "temperature": temperature,
                        }
                        if "qwen" in current_model.lower():
                            payload["max_tokens"] = 950
                        if use_strict_json:
                            payload["response_format"] = {"type": "json_object"}
                        if tools:
                            payload["tools"] = tools

                        async with httpx.AsyncClient(timeout=20.0) as client:
                            res = await client.post(url, headers=headers, json=payload)
                            if res.status_code == 429:
                                logger.warning(f"Groq model {current_model} rate limited (429). Switching to next model immediately...")
                                break
                            if res.status_code == 400 and ("json_validate_failed" in res.text or "Failed to validate JSON" in res.text):
                                logger.warning(f"Groq strict JSON validation failed on {current_model}. Retrying without strict response_format...")
                                if attempt < max_retries - 1:
                                    continue
                            if res.status_code != 200:
                                logger.warning(f"Groq API HTTP {res.status_code}: {res.text}")
                                break

                            data = res.json()
                            choice = data["choices"][0]["message"]
                            content = choice.get("content") or ""
                            tool_calls = choice.get("tool_calls")
                            usage = data.get("usage", {})
                            tokens = usage.get("total_tokens", 0)

                            return LLMResponse(
                                content=content,
                                tool_calls=tool_calls,
                                model_name=current_model,
                                tokens_used=tokens,
                                estimated_cost_usd=(tokens / 1000) * 0.0005,
                            )

                except Exception as e:
                    last_error = e
                    err_str = str(e)
                    logger.warning(f"Groq API ({current_model}) attempt {attempt + 1} error: {err_str}")
                    if "429" in err_str or "rate_limit" in err_str.lower() or "tpd" in err_str.lower() or "tokens per day" in err_str.lower():
                        logger.warning(f"Groq model {current_model} hit rate/token limit. Switching to alternative model immediately...")
                        break
                    if "json_validate_failed" in err_str or "Failed to validate JSON" in err_str:
                        logger.warning(f"Groq strict JSON validation failed on {current_model}. Retrying without strict response_format...")
                        if attempt < max_retries - 1:
                            continue
                    if attempt == max_retries - 1:
                        break
                    await asyncio.sleep(backoff)

        raise LLMProviderException("groq", f"Groq request failed across all candidate models: {last_error}")

