"""Computer Control Subsystem for Victor (Mouse, Keyboard, Screen, Window Management)."""

import ctypes
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple
from victor.tools.base import BaseTool, PermissionLevel


class ComputerController:
    """Native Windows & cross-platform computer automation layer."""

    @staticmethod
    def get_screen_size() -> Tuple[int, int]:
        if sys.platform == "win32":
            user32 = ctypes.windll.user32
            return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
        return (1920, 1080)

    @staticmethod
    def get_cursor_position() -> Tuple[int, int]:
        if sys.platform == "win32":
            class POINT(ctypes.Structure):
                _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
            pt = POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
            return (pt.x, pt.y)
        return (0, 0)

    @staticmethod
    def mouse_move(x: int, y: int):
        if sys.platform == "win32":
            ctypes.windll.user32.SetCursorPos(x, y)

    @staticmethod
    def mouse_click(x: Optional[int] = None, y: Optional[int] = None, button: str = "left", double: bool = False):
        if sys.platform == "win32":
            if x is not None and y is not None:
                ctypes.windll.user32.SetCursorPos(x, y)
                time.sleep(0.05)

            MOUSEEVENTF_LEFTDOWN = 0x0002
            MOUSEEVENTF_LEFTUP = 0x0004
            MOUSEEVENTF_RIGHTDOWN = 0x0008
            MOUSEEVENTF_RIGHTUP = 0x0010

            down = MOUSEEVENTF_RIGHTDOWN if button == "right" else MOUSEEVENTF_LEFTDOWN
            up = MOUSEEVENTF_RIGHTUP if button == "right" else MOUSEEVENTF_LEFTUP

            ctypes.windll.user32.mouse_event(down, 0, 0, 0, 0)
            time.sleep(0.05)
            ctypes.windll.user32.mouse_event(up, 0, 0, 0, 0)

            if double:
                time.sleep(0.1)
                ctypes.windll.user32.mouse_event(down, 0, 0, 0, 0)
                time.sleep(0.05)
                ctypes.windll.user32.mouse_event(up, 0, 0, 0, 0)

    @staticmethod
    def mouse_scroll(clicks: int):
        if sys.platform == "win32":
            MOUSEEVENTF_WHEEL = 0x0800
            WHEEL_DELTA = 120
            ctypes.windll.user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, clicks * WHEEL_DELTA, 0)

    @staticmethod
    def get_active_window_title() -> str:
        if sys.platform == "win32":
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
            return buff.value
        return "Unknown Window"


class ComputerTool(BaseTool):
    name = "computer"
    description = "Inspect and control the desktop computer: mouse movements, clicks, scrolling, and active window state."
    permission = PermissionLevel.CONTROLLED
    slash_command = "/click"
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["click", "move", "scroll", "window_info", "screen_info"],
                "description": "The computer control action to perform"
            },
            "x": {
                "type": "integer",
                "description": "X coordinate on screen"
            },
            "y": {
                "type": "integer",
                "description": "Y coordinate on screen"
            },
            "button": {
                "type": "string",
                "enum": ["left", "right"],
                "description": "Mouse button for click action (default: left)"
            },
            "double": {
                "type": "boolean",
                "description": "Whether to perform a double click"
            },
            "scroll_amount": {
                "type": "integer",
                "description": "Number of scroll clicks (positive for up, negative for down)"
            }
        },
        "required": ["action"]
    }

    async def run(
        self,
        action: str = "window_info",
        x: Optional[int] = None,
        y: Optional[int] = None,
        button: str = "left",
        double: bool = False,
        scroll_amount: int = -2,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        ctrl = ComputerController

        if action == "screen_info":
            width, height = ctrl.get_screen_size()
            curr_x, curr_y = ctrl.get_cursor_position()
            return {
                "action": "screen_info",
                "screen_width": width,
                "screen_height": height,
                "cursor_x": curr_x,
                "cursor_y": curr_y,
            }

        elif action == "window_info":
            title = ctrl.get_active_window_title()
            curr_x, curr_y = ctrl.get_cursor_position()
            return {
                "action": "window_info",
                "active_window": title,
                "cursor": {"x": curr_x, "y": curr_y},
            }

        elif action == "move":
            if x is None or y is None:
                raise ValueError("X and Y coordinates required for mouse move.")
            ctrl.mouse_move(x, y)
            return {"action": "move", "x": x, "y": y, "status": "success"}

        elif action == "click":
            ctrl.mouse_click(x=x, y=y, button=button, double=double)
            return {
                "action": "click",
                "x": x,
                "y": y,
                "button": button,
                "double": double,
                "status": "success",
            }

        elif action == "scroll":
            ctrl.mouse_scroll(scroll_amount)
            return {
                "action": "scroll",
                "amount": scroll_amount,
                "status": "success",
            }

        raise ValueError(f"Unknown computer action: '{action}'")

    def intent_patterns(self) -> list[dict]:
        def extract_click(m) -> dict:
            return {"action": "click", "x": int(m.group(1)), "y": int(m.group(2))}
            
        return [
            {"pattern": r"^(what is the active window|active window|what window is open|current window)$", "extract": {"action": "window_info"}},
            {"pattern": r"^(screen size|screen resolution|display size)$", "extract": {"action": "screen_info"}},
            {"pattern": r"^click\s+(?:mouse\s+)?(?:at\s+)?([0-9]+)[,\s]+([0-9]+)$", "extract": extract_click}
        ]

    def format_display(self, result) -> str:
        if not result.success:
            return f"I encountered an error executing {self.name}: {result.output}"
        out = result.output
        if isinstance(out, dict):
            act = out.get("action", "")
            if act == "click":
                return f"Clicked mouse at ({out.get('x')}, {out.get('y')})."
            elif act == "window_info":
                return f"Active window: \"{out.get('active_window', '')}\" at cursor ({out.get('cursor', {}).get('x')}, {out.get('cursor', {}).get('y')})."
            elif act == "screen_info":
                return f"Screen resolution: {out.get('screen_width')}x{out.get('screen_height')}."
            return f"Computer action '{act}' executed successfully."
        return str(out)

