from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class LLMMessage(BaseModel):
    role: str  # "system", "user", "assistant"
    content: str


class LLMResponse(BaseModel):
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    model_name: str
    tokens_used: int = 0
    estimated_cost_usd: float = 0.0


class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate_completion(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.2,
        tools: Optional[List[Dict[str, Any]]] = None,
        json_mode: bool = False,
    ) -> LLMResponse:
        """Generates text completion or tool call output from LLM provider."""
        pass
