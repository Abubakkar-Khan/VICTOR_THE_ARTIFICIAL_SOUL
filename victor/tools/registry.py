"""Central Tool Registry for Victor."""

from typing import Dict, List, Optional
from victor.core.config import SecurityConfig
from victor.tools.base import BaseTool, PermissionLevel, ToolResult


class ToolRegistry:
    """Registry that manages tools, permissions, and command lookups."""

    def __init__(self, security_config: Optional[SecurityConfig] = None):
        self._tools: Dict[str, BaseTool] = {}
        self._slash_commands: Dict[str, BaseTool] = {}
        self.security = security_config or SecurityConfig()

    def register(self, tool: BaseTool) -> BaseTool:
        """Register a tool instance."""
        self._tools[tool.name] = tool
        if tool.slash_command:
            # normalize command, e.g. /calc
            cmd = tool.slash_command.lower()
            if not cmd.startswith("/"):
                cmd = f"/{cmd}"
            self._slash_commands[cmd] = tool
        return tool

    def get(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return self._tools.get(name)

    def get_by_slash_command(self, cmd: str) -> Optional[BaseTool]:
        """Get a tool by its slash command shortcut (e.g. '/calc')."""
        return self._slash_commands.get(cmd.lower())

    def list_tools(self) -> List[BaseTool]:
        """Return all registered tools."""
        return list(self._tools.values())

    def check_permission(self, tool: BaseTool) -> bool:
        """Check if tool execution is permitted under current security policy."""
        if tool.permission == PermissionLevel.SAFE:
            return True
        if tool.permission == PermissionLevel.CONTROLLED:
            return True
        if tool.permission == PermissionLevel.DANGEROUS:
            return self.security.allow_shell
        return False

    async def execute_tool(self, name: str, **kwargs) -> ToolResult:
        """Execute a tool by name with permission gating."""
        tool = self.get(name)
        if not tool:
            return ToolResult(
                success=False,
                output=f"Tool '{name}' is not registered.",
                error="ToolNotFound"
            )

        if not self.check_permission(tool):
            return ToolResult(
                success=False,
                output=(
                    f"Permission denied: Tool '{name}' is marked as {tool.permission.value}. "
                    "Explicit authorization is required in security settings."
                ),
                error="PermissionDenied"
            )

        return await tool.execute(**kwargs)

    def format_all_descriptions(self) -> str:
        """Format all registered tools for system prompt injection."""
        return "\n".join(tool.format_description() for tool in self._tools.values())

    def to_schemas(self) -> List[Dict]:
        """Export all registered tools as schemas for API / UI / OpenAI function calls."""
        return [tool.to_schema_dict() for tool in self._tools.values()]


# Default global tool registry instance
default_registry = ToolRegistry()
