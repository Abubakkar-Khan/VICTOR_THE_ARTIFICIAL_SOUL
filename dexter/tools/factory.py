"""Factory to register and initialize standard tools for Victor."""

from typing import Optional
from dexter.core.config import VictorConfig
from dexter.tools.applications import ApplicationTool
from dexter.tools.base import BaseTool
from dexter.tools.browser import BrowserTool, WebFetchTool
from dexter.tools.calculator import CalculatorTool
from dexter.tools.computer import ComputerTool
from dexter.tools.filesystem import FilesystemTool
from dexter.tools.notifications import NotificationTool
from dexter.tools.process import ProcessTool
from dexter.tools.registry import ToolRegistry
from dexter.tools.shell import ExecTool, ShellTool
from dexter.tools.web_search import WebSearchTool
from dexter.tools.youtube import YouTubeTool

from dexter.tools.keyboard import KeyboardTool
from dexter.tools.window_manager import WindowManagerTool  
from dexter.tools.screen_observer import ScreenObserverTool


def create_tool_registry(config: Optional[VictorConfig] = None) -> ToolRegistry:
    """Create a ToolRegistry configured with standard tools and permissions."""
    security = config.security if config else None
    registry = ToolRegistry(security_config=security)

    # 1. Runtime / Execution (OpenClaw Standard)
    registry.register(ExecTool(), aliases=["/sh", "/shell"])
    registry.register(ShellTool())
    registry.register(ProcessTool(), aliases=["/ps"])

    # 2. Filesystem (OpenClaw Standard)
    allowed_roots = config.security.allowed_file_roots if config else ["."]
    registry.register(FilesystemTool(allowed_roots=allowed_roots))

    # 3. Web & Information (OpenClaw Standard)
    registry.register(WebSearchTool())
    registry.register(WebFetchTool(), aliases=["/browse"])
    registry.register(BrowserTool())
    registry.register(YouTubeTool())

    # 4. Desktop Automation & Screen Control (OpenClaw Standard)
    registry.register(ApplicationTool())
    registry.register(WindowManagerTool())
    registry.register(KeyboardTool())
    registry.register(ScreenObserverTool())
    registry.register(ComputerTool())

    # 5. Utilities
    registry.register(CalculatorTool())
    registry.register(NotificationTool())

    return registry
