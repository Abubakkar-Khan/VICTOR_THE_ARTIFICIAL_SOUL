"""Model Provider Factory for Victor."""

from typing import Optional
from dexter.core.config import ModelConfig
from dexter.models.base import BaseLLM
from dexter.models.ollama import OllamaProvider
from dexter.models.remote import RemoteOpenAIProvider


def create_model_provider(config: Optional[ModelConfig] = None) -> BaseLLM:
    """Instantiate the appropriate ModelProvider based on configuration."""
    cfg = config or ModelConfig()
    provider_type = cfg.provider.lower()

    if provider_type == "ollama":
        return OllamaProvider(
            model_name=cfg.name,
            api_base=cfg.api_base,
            fallback_model=cfg.fallback_model,
            temperature=cfg.temperature,
            max_tokens=cfg.max_tokens,
        )
    elif provider_type in ["remote", "openai", "groq", "openrouter"]:
        return RemoteOpenAIProvider(
            model_name=cfg.name,
            api_base=cfg.api_base if cfg.api_base != "http://127.0.0.1:11434" else "https://api.openai.com/v1",
            temperature=cfg.temperature,
            max_tokens=cfg.max_tokens,
        )
    else:
        # Default to OllamaProvider
        return OllamaProvider(model_name=cfg.name)
