"""Configuration manager for Victor."""

import sys
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


class DexterConfig(BaseModel):
    name: str = "Dexter"
    title: str = "The Artificial Soul"
    tagline: str = "A small artificial mind with a world of tools."
    personality: PersonalityConfig = Field(default_factory=PersonalityConfig)
    behavior: BehaviorConfig = Field(default_factory=BehaviorConfig)
    model: ModelConfig = Field(default_factory=ModelConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)


# Backward compatibility alias
VictorConfig = DexterConfig


def find_config_path(override_path: Optional[str] = None) -> Path:
    if override_path and Path(override_path).exists():
        return Path(override_path)
    
    candidates = []
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        candidates.append(Path(sys._MEIPASS) / "config" / "dexter.yaml")
        candidates.append(Path(sys._MEIPASS) / "config" / "victor.yaml")
    
    base_dir = Path(__file__).resolve().parent.parent.parent
    candidates.extend([
        Path("config/dexter.yaml"),
        Path("config/victor.yaml"),
        Path("../config/dexter.yaml"),
        Path("../config/victor.yaml"),
        base_dir / "config" / "dexter.yaml",
        base_dir / "config" / "victor.yaml",
    ])
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    
    return Path("config/dexter.yaml")


def load_config(override_path: Optional[str] = None) -> DexterConfig:
    config_path = find_config_path(override_path)
    if not config_path.exists():
        return DexterConfig()
    
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    
    return DexterConfig(**data)
