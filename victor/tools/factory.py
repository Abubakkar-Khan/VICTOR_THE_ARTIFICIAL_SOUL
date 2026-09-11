"""Factory to register and initialize standard tools for Victor."""

from typing import Optional
from victor.core.config import VictorConfig
from victor.tools.applications import ApplicationTool
from victor.tools.base import BaseTool
from victor.tools.browser import BrowserTool
from victor.tools.calculator import CalculatorTool
from victor.tools.computer import ComputerTool
from victor.tools.filesystem import FilesystemTool
from victor.tools.notifications import NotificationTool
from victor.tools.registry import ToolRegistry
from victor.tools.shell import ShellTool
from victor.tools.web_search import WebSearchTool
from victor.tools.youtube import YouTubeTool


def create_tool_registry(config: Optional[VictorConfig] = None) -> ToolRegistry:
    """Create a ToolRegistry configured with standard tools and permissions."""
    security = config.security if config else None
    registry = ToolRegistry(security_config=security)

    # Register standard capabilities
    registry.register(CalculatorTool())
    registry.register(WebSearchTool())
    registry.register(BrowserTool())
    registry.register(YouTubeTool())
    registry.register(ApplicationTool())
    registry.register(ComputerTool())
    registry.register(NotificationTool())

    allowed_roots = config.security.allowed_file_roots if config else ["."]
    registry.register(FilesystemTool(allowed_roots=allowed_roots))
    registry.register(ShellTool())

    return registry
