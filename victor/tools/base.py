"""Standardized Tool Contract for Victor."""

from abc import ABC, abstractmethod
from enum import Enum
import json
import time
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class PermissionLevel(str, Enum):
    SAFE = "SAFE"
    CONTROLLED = "CONTROLLED"
    DANGEROUS = "DANGEROUS"


class ToolResult(BaseModel):
    """Standard execution result returned by all tools."""
    success: bool
    output: Any
    error: Optional[str] = None
    duration: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_summary_string(self, max_length: int = 4000) -> str:
        """Format the result cleanly for the LLM context."""
        if not self.success:
            return f"Error ({self.error}): {self.output}"
        
        if isinstance(self.output, (dict, list)):
            text = json.dumps(self.output, indent=2, ensure_ascii=False)
        else:
            text = str(self.output)
            
        if len(text) > max_length:
            return text[:max_length] + f"\n... [Truncated: {len(text) - max_length} characters omitted]"
        return text


class BaseTool(ABC):
    """Abstract base class for all Victor tools."""
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema specification
    permission: PermissionLevel = PermissionLevel.SAFE
    slash_command: Optional[str] = None

    @abstractmethod
    async def run(self, **kwargs: Any) -> Any:
        """Core execution logic implemented by subclasses."""
        pass

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Executes the tool with timing, error handling, and structured output."""
        start_time = time.perf_counter()
        try:
            output = await self.run(**kwargs)
            duration = time.perf_counter() - start_time
            return ToolResult(
                success=True,
                output=output,
                duration=round(duration, 3)
            )
        except Exception as e:
            duration = time.perf_counter() - start_time
            return ToolResult(
                success=False,
                output=str(e),
                error=type(e).__name__,
                duration=round(duration, 3)
            )

    def to_schema_dict(self) -> Dict[str, Any]:
        """Convert tool to standard tool definition format."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "permission": self.permission.value,
            "slash_command": self.slash_command,
        }

    def format_description(self) -> str:
        """Formats the tool for injection into the system prompt."""
        cmd_str = f" (Slash: {self.slash_command})" if self.slash_command else ""
        param_desc = ", ".join(f"{k}: {v.get('type', 'any')}" for k, v in self.parameters.get("properties", {}).items())
        return f"- `{self.name}`{cmd_str} [{self.permission.value}]: {self.description}. Parameters: ({param_desc})"

    def intent_patterns(self) -> list[dict]:
        """Return list of intent regex dicts for routing. E.g. {"pattern": r"regex", "extract": "param_name"}"""
        return []

    def format_display(self, result: ToolResult) -> str:
        """Return a clean, human-friendly string for displaying this tool's output."""
        return result.to_summary_string(max_length=1500)
