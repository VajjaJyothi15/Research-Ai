import json
from typing import Any, Dict, List, Optional
import httpx
from app.core.config import settings
from app.core.exceptions import LLMProviderException
from app.core.logging import logger
from app.providers.base import BaseLLMProvider, LLMMessage, LLMResponse


class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key if api_key is not None else settings.OPENAI_API_KEY
        self.model_name = model_name or settings.LLM_MODEL or "gpt-4o"

    async def generate_completion(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.2,
        tools: Optional[List[Dict[str, Any]]] = None,
        json_mode: bool = False,
    ) -> LLMResponse:
        if not self.api_key:
            raise LLMProviderException(
                "openai",
                "OpenAI API key is not configured. Please set the OPENAI_API_KEY environment variable in your .env file."
            )

        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        formatted_messages = [{"role": m.role, "content": m.content} for m in messages]
        payload: Dict[str, Any] = {
            "model": self.model_name,
            "messages": formatted_messages,
            "temperature": temperature,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        if tools:
            payload["tools"] = tools

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                res = await client.post(url, headers=headers, json=payload)
                if res.status_code != 200:
                    raise LLMProviderException("openai", f"HTTP {res.status_code}: {res.text}")
                data = res.json()
                
                choice = data["choices"][0]["message"]
                content = choice.get("content") or ""
                tool_calls = choice.get("tool_calls")
                
                usage = data.get("usage", {})
                tokens = usage.get("total_tokens", 0)

                return LLMResponse(
                    content=content,
                    tool_calls=tool_calls,
                    model_name=self.model_name,
                    tokens_used=tokens,
                    estimated_cost_usd=(tokens / 1000) * 0.002,
                )
            except Exception as e:
                logger.error(f"OpenAI API error: {e}")
                raise LLMProviderException("openai", str(e))
