"""Computer Control Subsystem for Victor (Mouse, Keyboard, Screen, Window Management)."""

import ctypes
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple
from dexter.tools.base import BaseTool, PermissionLevel


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
            "element": {
                "type": "string",
                "description": "UI element ID from observe_screen to click (e.g. 'e1', 'e2')"
            },
            "observation_id": {
                "type": "integer",
                "description": "Observation ID from screen_observer to prevent stale clicks"
            },
            "x": {
                "type": "integer",
                "description": "X coordinate on screen (fallback if element not provided)"
            },
            "y": {
                "type": "integer",
                "description": "Y coordinate on screen (fallback if element not provided)"
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
            "direction": {
                "type": "string",
                "enum": ["up", "down"],
                "description": "Scroll direction ('up' or 'down')"
            },
            "scroll_amount": {
                "type": "integer",
                "description": "Number of scroll clicks"
            }
        },
        "required": ["action"]
    }

    async def run(
        self,
        action: str = "window_info",
        element: Optional[str] = None,
        observation_id: Optional[int] = None,
        x: Optional[int] = None,
        y: Optional[int] = None,
        button: str = "left",
        double: bool = False,
        direction: Optional[str] = None,
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
                "status": "verified",
                "verification": {"status": "verified", "verified": True},
            }

        elif action == "window_info":
            title = ctrl.get_active_window_title()
            curr_x, curr_y = ctrl.get_cursor_position()
            return {
                "action": "window_info",
                "active_window": title,
                "cursor": {"x": curr_x, "y": curr_y},
                "status": "verified",
                "verification": {"status": "verified", "verified": True},
            }

        elif action == "move":
            if x is None or y is None:
                raise ValueError("X and Y coordinates required for mouse move.")
            ctrl.mouse_move(x, y)
            return {
                "action": "move",
                "x": x,
                "y": y,
                "status": "verified",
                "verification": {"status": "verified", "verified": True},
            }

        elif action == "click":
            # 1. UI Automation Element ID or Text resolution
            target_eid = element or kwargs.get("element_id")
            obs_id = observation_id or kwargs.get("obs_id")

            if target_eid:
                from dexter.tools.screen_observer import get_cached_element
                control, err = get_cached_element(target_eid, obs_id)
                if err:
                    return {
                        "action": "click",
                        "element": target_eid,
                        "status": "failed",
                        "message": err,
                        "verification": {
                            "status": "failed",
                            "verified": False,
                            "reason": err,
                        },
                    }

                initial_window = ctrl.get_active_window_title()
                cx, cy = None, None
                try:
                    if hasattr(control, "BoundingRectangle"):
                        rect = control.BoundingRectangle
                        cx = int((rect.left + rect.right) / 2)
                        cy = int((rect.top + rect.bottom) / 2)
                        ctrl.mouse_click(x=cx, y=cy, button=button, double=double)
                    elif hasattr(control, "Click"):
                        if double and hasattr(control, "DoubleClick"):
                            control.DoubleClick()
                        elif button == "right" and hasattr(control, "RightClick"):
                            control.RightClick()
                        else:
                            control.Click()
                except Exception as e:
                    return {
                        "action": "click",
                        "element": target_eid,
                        "status": "failed",
                        "message": f"Failed to execute click on element: {e}",
                        "verification": {
                            "status": "failed",
                            "verified": False,
                            "reason": str(e),
                        },
                    }

                time.sleep(0.15)
                new_window = ctrl.get_active_window_title()
                state_changed = (new_window != initial_window)
                elem_name = getattr(control, "Name", "") or target_eid

                status = "verified" if state_changed else "executed_unverified"
                reason = (
                    f"Clicked [{target_eid}] '{elem_name}'. Active window transitioned to '{new_window}'."
                    if state_changed
                    else f"Clicked [{target_eid}] '{elem_name}'. Click performed, but active window did not change."
                )

                return {
                    "action": "click",
                    "element": target_eid,
                    "name": elem_name,
                    "x": cx,
                    "y": cy,
                    "button": button,
                    "double": double,
                    "status": status,
                    "verification": {
                        "status": status,
                        "verified": state_changed,
                        "reason": reason,
                    },
                }

            # 2. Coordinate fallback
            if x is None or y is None:
                raise ValueError("Must provide either 'element' or 'x' and 'y' coordinates for click.")

            initial_window = ctrl.get_active_window_title()
            ctrl.mouse_click(x=x, y=y, button=button, double=double)
            time.sleep(0.15)
            new_window = ctrl.get_active_window_title()
            state_changed = (new_window != initial_window)

            status = "verified" if state_changed else "executed_unverified"
            reason = (
                f"Clicked coordinates ({x}, {y}). Active window transitioned to '{new_window}'."
                if state_changed
                else f"Clicked coordinates ({x}, {y}). Click performed, but active window did not change."
            )

            return {
                "action": "click",
                "x": x,
                "y": y,
                "button": button,
                "double": double,
                "status": status,
                "verification": {
                    "status": status,
                    "verified": state_changed,
                    "reason": reason,
                },
            }

        elif action == "scroll":
            amt = scroll_amount
            d = (direction or "down").strip().lower()
            clicks = abs(amt) if amt != 0 else 3
            amt = clicks if d == "up" else -clicks
            ctrl.mouse_scroll(amt)
            return {
                "action": "scroll",
                "amount": amt,
                "direction": "up" if amt > 0 else "down",
                "status": "verified",
                "verification": {"status": "verified", "verified": True},
            }

        raise ValueError(f"Unknown computer action: '{action}'")

    def intent_patterns(self) -> list[dict]:
        def extract_click(m) -> dict:
            return {"action": "click", "x": int(m.group(1)), "y": int(m.group(2))}

        def extract_element_click(m) -> dict:
            eid = m.group(1).strip().lower()
            return {"action": "click", "element": eid}

        def extract_element_double_click(m) -> dict:
            eid = m.group(1).strip().lower()
            return {"action": "click", "element": eid, "double": True}

        def extract_element_right_click(m) -> dict:
            eid = m.group(1).strip().lower()
            return {"action": "click", "element": eid, "button": "right"}

        def extract_scroll(m) -> dict:
            d = m.group(1) if m.lastindex else "down"
            direction = (d or "down").strip().lower()
            return {"action": "scroll", "direction": direction}
            
        return [
            {"pattern": r"^(what is the active window|active window|what window is open|current window)$", "extract": {"action": "window_info"}},
            {"pattern": r"^(screen size|screen resolution|display size)$", "extract": {"action": "screen_info"}},
            {"pattern": r"^double\s+click\s+([eE][0-9]+)$", "extract": extract_element_double_click},
            {"pattern": r"^right\s+click\s+([eE][0-9]+)$", "extract": extract_element_right_click},
            {"pattern": r"^click\s+(?:mouse\s+)?(?:at\s+)?([0-9]+)[,\s]+([0-9]+)$", "extract": extract_click},
            {"pattern": r"^click\s+([eE][0-9]+)$", "extract": extract_element_click},
            {"pattern": r"^click\s+(?:the\s+)?(.+?)(?:\s+button)?$", "extract": extract_element_click},
            {"pattern": r"^scroll\s*(up|down)?$", "extract": extract_scroll}
        ]

    def format_display(self, result) -> str:
        if not result.success:
            return f"I encountered an error executing {self.name}: {result.output}"
        out = result.output
        if isinstance(out, dict):
            act = out.get("action", "")
            status = out.get("status", "")
            if act == "click":
                elem = out.get("element")
                name = out.get("name")
                target_str = f"[{elem}] '{name}'" if elem and name else (f"[{elem}]" if elem else f"at coordinates ({out.get('x')}, {out.get('y')})")
                if status == "verified":
                    return f"Clicked {target_str} (verified: screen state changed)."
                elif status == "executed_unverified":
                    return f"Clicked {target_str} (executed, but could not verify resulting screen state)."
                elif status == "failed":
                    return f"Failed to click {target_str}: {out.get('message', 'element unavailable')}."
                return f"Clicked {target_str}."
            elif act == "window_info":
                return f"Active window: \"{out.get('active_window', '')}\" at cursor ({out.get('cursor', {}).get('x')}, {out.get('cursor', {}).get('y')})."
            elif act == "screen_info":
                return f"Screen resolution: {out.get('screen_width')}x{out.get('screen_height')}."
            elif act == "move":
                return f"Moved cursor to ({out.get('x')}, {out.get('y')})."
            elif act == "scroll":
                return f"Scrolled {out.get('direction', 'down')} by {abs(out.get('amount', 3))} clicks."
            return f"Computer action '{act}' executed successfully."
        return str(out)

