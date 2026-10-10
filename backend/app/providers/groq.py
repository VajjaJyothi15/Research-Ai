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
            self._client = AsyncGroq(api_key=self.api_key, timeout=60.0)

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

        # Retry configuration
        max_retries = 3
        backoff = 1.5

        # Fallback list of models available on Groq
        models_to_try = [self.model_name]
        for alt in ["openai/gpt-oss-20b", "openai/gpt-oss-120b", "qwen/qwen3.8-27b", "allam-2-7b"]:
            if alt not in models_to_try:
                models_to_try.append(alt)

        last_error = None
        for current_model in models_to_try:
            for attempt in range(max_retries):
                # On subsequent retries if json_mode failed, disable strict response_format
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
                        if use_strict_json:
                            kwargs["response_format"] = {"type": "json_object"}
                        if tools:
                            kwargs["tools"] = tools

                        completion = await self._client.chat.completions.create(**kwargs)
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
                        if use_strict_json:
                            payload["response_format"] = {"type": "json_object"}
                        if tools:
                            payload["tools"] = tools

                        async with httpx.AsyncClient(timeout=60.0) as client:
                            res = await client.post(url, headers=headers, json=payload)
                            if res.status_code == 429:
                                if "TPD" in res.text or "tokens per day" in res.text or "daily" in res.text.lower():
                                    logger.warning(f"Groq model {current_model} exceeded daily token limit. Switching to fallback model...")
                                    break  # Switch to next model immediately
                                if attempt < max_retries - 1:
                                    await asyncio.sleep(backoff * (attempt + 1))
                                    continue
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
                    if "TPD" in err_str or "tokens per day" in err_str or "daily" in err_str.lower():
                        logger.warning(f"Groq model {current_model} reached daily token limit. Switching to alternative model...")
                        break  # Try next model in list immediately
                    if "json_validate_failed" in err_str or "Failed to validate JSON" in err_str:
                        logger.warning(f"Groq strict JSON validation failed on {current_model}. Retrying without strict response_format...")
                        if attempt < max_retries - 1:
                            continue
                    if "rate_limit" in err_str.lower() or "429" in err_str:
                        sleep_time = 1.5 * (attempt + 1)
                        match_m = re.search(r"try again in (\d+)m([\d\.]+)s", err_str)
                        match_s = re.search(r"try again in ([\d\.]+)s", err_str)
                        if match_m:
                            sleep_time = int(match_m.group(1)) * 60 + float(match_m.group(2)) + 0.5
                        elif match_s:
                            sleep_time = float(match_s.group(1)) + 0.5
                        sleep_time = min(sleep_time, 15.0)

                        if attempt < max_retries - 1:
                            logger.info(f"Rate limited by Groq API. Sleeping for {sleep_time:.2f}s before retry...")
                            await asyncio.sleep(sleep_time)
                            continue
                        break
                    if attempt == max_retries - 1:
                        break
                    await asyncio.sleep(backoff * (attempt + 1))

        raise LLMProviderException("groq", f"Groq request failed across all candidate models: {last_error}")

