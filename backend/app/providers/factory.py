from typing import Any, Dict, List, Optional
from app.core.config import settings
from app.core.exceptions import LLMProviderException
from app.core.logging import logger
from app.providers.base import BaseLLMProvider, LLMMessage, LLMResponse
from app.providers.gemini import GeminiProvider
from app.providers.groq import GroqProvider
from app.providers.openai import OpenAIProvider


class ResilientFallbackProvider(BaseLLMProvider):
    def __init__(self, primary: BaseLLMProvider, fallback: Optional[BaseLLMProvider] = None):
        self.primary = primary
        self.fallback = fallback

    async def generate_completion(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.2,
        tools: Optional[List[Dict[str, Any]]] = None,
        json_mode: bool = False,
    ) -> LLMResponse:
        try:
            return await self.primary.generate_completion(
                messages=messages,
                temperature=temperature,
                tools=tools,
                json_mode=json_mode,
            )
        except Exception as e:
            if self.fallback:
                logger.warning(f"Primary LLM provider failed ({e}), falling back to secondary provider...")
                return await self.fallback.generate_completion(
                    messages=messages,
                    temperature=temperature,
                    tools=tools,
                    json_mode=json_mode,
                )
            raise


def get_llm_provider(provider_name: str | None = None) -> BaseLLMProvider:
    name = (provider_name or settings.LLM_PROVIDER or "groq").lower()
    if name == "groq":
        primary = GroqProvider()
        fallback = GeminiProvider() if settings.GEMINI_API_KEY else None
        return ResilientFallbackProvider(primary, fallback)
    elif name == "gemini":
        primary = GeminiProvider()
        fallback = GroqProvider() if settings.GROQ_API_KEY else None
        return ResilientFallbackProvider(primary, fallback)
    elif name == "openai":
        return OpenAIProvider()
    else:
        raise LLMProviderException(
            name,
            f"Unsupported LLM provider '{name}'. Supported providers: 'groq', 'gemini', 'openai'."
        )


