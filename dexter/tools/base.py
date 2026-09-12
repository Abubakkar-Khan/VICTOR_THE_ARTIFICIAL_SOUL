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
    status: str = "verified"  # "verified", "executed_unverified", "failed", "timeout"
    verification: Dict[str, Any] = Field(default_factory=dict)
    target: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_summary_string(self, max_length: int = 4000) -> str:
        """Format the result cleanly for the LLM context."""
        status_tag = f"Status: {self.status.upper()}"
        if not self.success or self.status in ["failed", "timeout"]:
            err_msg = self.error or "Action failed"
            return f"[{status_tag}] Error ({err_msg}): {self.output}"

        if self.status == "executed_unverified":
            prefix = f"[{status_tag}] The command was executed, but resulting state could not be verified.\n"
        else:
            prefix = f"[{status_tag}]\n"

        if isinstance(self.output, (dict, list)):
            text = json.dumps(self.output, indent=2, ensure_ascii=False)
        else:
            text = str(self.output)

        full = prefix + text
        if len(full) > max_length:
            return full[:max_length] + f"\n... [Truncated: {len(full) - max_length} characters omitted]"
        return full


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

            status = "verified"
            verification = {}
            target = kwargs.get("app_name") or kwargs.get("title") or kwargs.get("path") or kwargs.get("target") or None
            success = True

            if isinstance(output, dict):
                if "verification" in output and isinstance(output["verification"], dict):
                    verification = output["verification"]
                    status = verification.get("status", "verified")
                elif "status" in output:
                    raw_status = str(output["status"]).lower()
                    if raw_status in ["failed", "timeout"]:
                        status = raw_status
                    elif raw_status == "error":
                        status = "failed"
                    elif raw_status in ["executed_unverified", "unverified"]:
                        status = "executed_unverified"
                    elif raw_status in ["verified", "success", "edited", "appended", "created", "opened", "renamed", "moved", "copied"]:
                        status = "verified"

                if "success" in output and isinstance(output["success"], bool):
                    success = output["success"]
                if "target" in output and isinstance(output["target"], str):
                    target = output["target"]

            return ToolResult(
                success=success,
                output=output,
                status=status,
                verification=verification,
                target=target,
                duration=round(duration, 3)
            )
        except Exception as e:
            duration = time.perf_counter() - start_time
            return ToolResult(
                success=False,
                output=str(e),
                error=type(e).__name__,
                status="failed",
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
