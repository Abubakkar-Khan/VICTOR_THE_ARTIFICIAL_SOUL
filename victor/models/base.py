"""Abstract base LLM interface for Victor."""

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Unified message format across models."""
    role: str  # 'system', 'user', 'assistant', 'tool'
    content: str
    name: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LLMResponse(BaseModel):
    """Response returned by model execution."""
    content: str
    model: str
    duration: float = 0.0
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseLLM(ABC):
    """Abstract model provider interface."""

    def __init__(self, model_name: str, api_base: str = "", temperature: float = 0.7, max_tokens: int = 1024):
        self.model_name = model_name
        self.api_base = api_base
        self.temperature = temperature
        self.max_tokens = max_tokens

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if provider and model are ready and accessible."""
        pass

    @abstractmethod
    async def generate(
        self,
        messages: List[ChatMessage],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Generate a complete response from the model."""
        pass

    @abstractmethod
    async def stream(
        self,
        messages: List[ChatMessage],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """Stream response tokens from the model as they arrive."""
        pass
