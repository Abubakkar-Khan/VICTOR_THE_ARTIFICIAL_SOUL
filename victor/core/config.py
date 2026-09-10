"""Configuration manager for Victor."""

import os
from pathlib import Path
from typing import List, Optional
import yaml
from pydantic import BaseModel, Field


class PersonalityConfig(BaseModel):
    curiosity: str = "high"
    humor: str = "medium"
    formality: str = "low"
    enthusiasm: str = "medium"
    tone: str = (
        "Curious, slightly eccentric, intelligent, occasionally unsettling, but fundamentally helpful."
    )


class BehaviorConfig(BaseModel):
    concise: bool = True
    explain_tools: bool = True
    acknowledge_errors: bool = True
    no_emojis: bool = True
    max_response_sentences: int = 3


class ModelConfig(BaseModel):
    provider: str = "ollama"
    name: str = "qwen2:1.5b"
    fallback_model: str = "qwen3.5:2b"
    api_base: str = "http://127.0.0.1:11434"
    temperature: float = 0.7
    max_tokens: int = 1024


class SecurityConfig(BaseModel):
    allow_shell: bool = False
    allowed_file_roots: List[str] = Field(default_factory=lambda: ["."])


class VictorConfig(BaseModel):
    name: str = "Victor"
    title: str = "The Artificial Soul"
    tagline: str = "A small artificial mind with a world of tools."
    personality: PersonalityConfig = Field(default_factory=PersonalityConfig)
    behavior: BehaviorConfig = Field(default_factory=BehaviorConfig)
    model: ModelConfig = Field(default_factory=ModelConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)


def find_config_path(override_path: Optional[str] = None) -> Path:
    if override_path and Path(override_path).exists():
        return Path(override_path)
    
    candidates = [
        Path("config/victor.yaml"),
        Path("../config/victor.yaml"),
        Path(__file__).resolve().parent.parent.parent / "config" / "victor.yaml",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    
    return Path("config/victor.yaml")


def load_config(override_path: Optional[str] = None) -> VictorConfig:
    config_path = find_config_path(override_path)
    if not config_path.exists():
        return VictorConfig()
    
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    
    return VictorConfig(**data)
