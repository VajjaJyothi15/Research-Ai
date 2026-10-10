import asyncio
import json
from typing import Any, Dict, List, Optional
import httpx
from app.core.config import settings
from app.core.exceptions import LLMProviderException
from app.core.logging import logger
from app.providers.base import BaseLLMProvider, LLMMessage, LLMResponse


class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key if api_key is not None else settings.GEMINI_API_KEY
        m = model_name or settings.LLM_MODEL
        if not m or not m.startswith("gemini"):
            m = "gemini-3.8-flash"
        self.model_name = m

    async def generate_completion(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.2,
        tools: Optional[List[Dict[str, Any]]] = None,
        json_mode: bool = False,
    ) -> LLMResponse:
        if not self.api_key:
            raise LLMProviderException(
                "gemini",
                "Gemini API key is not configured. Please set the GEMINI_API_KEY environment variable in your .env file."
            )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"

        contents = []
        system_instruction = None

        for msg in messages:
            if msg.role == "system":
                system_instruction = {"parts": [{"text": msg.content}]}
            elif msg.role == "user":
                contents.append({"role": "user", "parts": [{"text": msg.content}]})
            elif msg.role == "assistant":
                contents.append({"role": "model", "parts": [{"text": msg.content}]})

        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
            }
        }
        if system_instruction:
            payload["systemInstruction"] = system_instruction
        if json_mode:
            payload["generationConfig"]["responseMimeType"] = "application/json"

        max_retries = 5
        for attempt in range(max_retries):
            async with httpx.AsyncClient(timeout=60.0) as client:
                try:
                    res = await client.post(url, json=payload)
                    if res.status_code == 429:
                        if attempt < max_retries - 1:
                            await asyncio.sleep(3.0 * (attempt + 1))
                            continue
                        raise LLMProviderException("gemini", "Gemini API rate limit reached.")
                    if res.status_code != 200:
                        raise LLMProviderException("gemini", f"HTTP {res.status_code}: {res.text}")
                    data = res.json()
                    
                    candidates = data.get("candidates", [])
                    if not candidates:
                        raise LLMProviderException("gemini", "No response candidates returned")

                    parts = candidates[0].get("content", {}).get("parts", [])
                    text_content = "".join([p.get("text", "") for p in parts if "text" in p])
                    
                    usage = data.get("usageMetadata", {})
                    tokens = usage.get("totalTokenCount", 0)

                    return LLMResponse(
                        content=text_content,
                        model_name=self.model_name,
                        tokens_used=tokens,
                        estimated_cost_usd=(tokens / 1000) * 0.0001,
                    )
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"Gemini API error: {e}")
                        raise LLMProviderException("gemini", str(e))
                    await asyncio.sleep(3.0 * (attempt + 1))
