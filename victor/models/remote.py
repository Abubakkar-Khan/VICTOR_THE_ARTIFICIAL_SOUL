"""Remote OpenAI-compatible Model Provider for Victor."""

import os
import time
from typing import Any, AsyncIterator, Dict, List, Optional
import httpx
from victor.models.base import BaseLLM, ChatMessage, LLMResponse


class RemoteOpenAIProvider(BaseLLM):
    """Integrates Victor with remote OpenAI-compatible endpoints (OpenAI, Groq, OpenRouter, LocalAI, vLLM)."""

    def __init__(
        self,
        model_name: str = "gpt-4o-mini",
        api_base: str = "https://api.openai.com/v1",
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ):
        super().__init__(
            model_name=model_name,
            api_base=api_base.rstrip("/"),
            temperature=temperature,
            max_tokens=max_tokens,
        )
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")

    async def is_available(self) -> bool:
        return bool(self.api_key or "localhost" in self.api_base or "127.0.0.1" in self.api_base)

    async def generate(
        self,
        messages: List[ChatMessage],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        start = time.perf_counter()
        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        formatted_messages = []
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})
        for msg in messages:
            formatted_messages.append({"role": msg.role, "content": msg.content})

        payload = {
            "model": self.model_name,
            "messages": formatted_messages,
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens or self.max_tokens,
            "stream": False,
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                res = await client.post(f"{self.api_base}/chat/completions", headers=headers, json=payload)
                if res.status_code != 200:
                    return LLMResponse(
                        content=f"[Remote API Error {res.status_code}]: {res.text}",
                        model=self.model_name,
                        duration=round(time.perf_counter() - start, 3),
                    )
                data = res.json()
                content = data["choices"][0]["message"]["content"]
                return LLMResponse(
                    content=content,
                    model=self.model_name,
                    duration=round(time.perf_counter() - start, 3),
                )
        except Exception as e:
            return LLMResponse(
                content=f"[Remote API Exception]: {str(e)}",
                model=self.model_name,
                duration=round(time.perf_counter() - start, 3),
            )

    async def stream(
        self,
        messages: List[ChatMessage],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        # Simple non-stream fallback or token yield for compatibility
        res = await self.generate(messages, system_prompt, temperature, max_tokens)
        yield res.content
