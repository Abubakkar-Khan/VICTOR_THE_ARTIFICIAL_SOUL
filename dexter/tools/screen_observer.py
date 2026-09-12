"""Screen Observer Tool for Victor (Windows UI Automation & Accessibility Tree).

Provides compact, structured screen perceptions with stable observation IDs and
deterministic control filtering optimized for a ~1.5B local LLM.
"""

import ctypes
import os
import tempfile
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from dexter.tools.base import BaseTool, PermissionLevel
from dexter.tools.verifier import (
    get_window_process_name,
    get_window_title,
    wait_for_condition_async,
)

user32 = ctypes.windll.user32 if hasattr(ctypes, "windll") else None
gdi32 = ctypes.windll.gdi32 if hasattr(ctypes, "windll") else None

try:
    import uiautomation as auto
    HAS_UIAUTOMATION = True
except ImportError:
    HAS_UIAUTOMATION = False


# Module-level observation cache
_current_observation_id: int = 0
_observation_store: Dict[int, Dict[str, Any]] = {}
_element_cache: Dict[str, Any] = {}  # Active observation cache for backward compatibility


def get_current_observation_id() -> int:
    """Return the active screen observation sequence ID."""
    global _current_observation_id
    return _current_observation_id


def get_cached_element(eid: str, obs_id: Optional[int] = None) -> Tuple[Optional[Any], Optional[str]]:
    """Retrieve an element from cache with strict stale-observation validation."""
    global _current_observation_id, _observation_store, _element_cache
    eid = eid.strip().lower()

    if obs_id is not None and obs_id != _current_observation_id:
        return None, (
            f"Element [{eid}] belongs to outdated screen observation #{obs_id} "
            f"(current observation is #{_current_observation_id}). Please observe the screen again."
        )

    # Check active observation store
    curr_elements = _observation_store.get(_current_observation_id, _element_cache)
    control = curr_elements.get(eid)
    if control:
        return control, None

    # Search by text match if exact ID not found
    for k, ctrl_item in curr_elements.items():
        try:
            name = getattr(ctrl_item, "Name", "") or ""
            if eid in name.lower():
                return ctrl_item, None
        except Exception:
            pass

    return None, f"Element [{eid}] not found in active screen observation #{_current_observation_id}. Observe the screen to get current elements."


async def wait_for_ui_state(
    predicate: Callable[[], bool],
    timeout: float = 5.0,
    poll_interval: float = 0.25,
) -> bool:
    """Wait until a UI predicate condition evaluates to True."""
    success, _ = await wait_for_condition_async(predicate, timeout=timeout, poll_interval=poll_interval)
    return bool(success)


class ScreenObserverTool(BaseTool):
    name = "screen_observer"
    description = "Screen understanding via Windows UI Automation accessibility tree and screenshots."
    permission = PermissionLevel.SAFE
    slash_command = "/observe"
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["observe_screen", "find_element", "take_screenshot"],
                "description": "Action to perform."
            },
            "name": {
                "type": "string",
                "description": "Name or text of the element to find (for find_element)."
            },
            "observation_id": {
                "type": "integer",
                "description": "Optional observation sequence ID to validate against."
            }
        },
        "required": ["action"]
    }

    def intent_patterns(self) -> list[dict]:
        return [
            {"pattern": r'^(?:what is on screen|observe screen|what do you see|screen observation)$', "extract": {"action": "observe_screen"}},
            {"pattern": r'^(?:take screenshot|screenshot)$', "extract": {"action": "take_screenshot"}},
            {"pattern": r'^find\s+(.+)\s+on screen$', "extract": lambda m: {"action": "find_element", "name": m.group(1).strip()}}
        ]

    async def run(self, **kwargs) -> Any:
        action = kwargs.get("action", "observe_screen")

        if action == "observe_screen":
            global _current_observation_id, _observation_store, _element_cache
            _current_observation_id += 1
            obs_id = _current_observation_id
            active_cache: Dict[str, Any] = {}

            if not HAS_UIAUTOMATION or not user32:
                hwnd = user32.GetForegroundWindow() if user32 else 0
                title = get_window_title(hwnd) if hwnd else "Desktop"
                proc_name = get_window_process_name(hwnd) if hwnd else "explorer.exe"
                out_text = (
                    f"OBSERVATION_ID: {obs_id}\n"
                    f"ACTIVE WINDOW:\n"
                    f"  Title: {title}\n"
                    f"  Process: {proc_name}\n"
                    f"VISIBLE INTERACTIVE ELEMENTS:\n"
                    f"  [e1] window: {title}\n"
                    f"  (uiautomation library not installed - using Win32 window headers)"
                )
                active_cache["e1"] = None
                _observation_store[obs_id] = active_cache
                _element_cache = active_cache
                return {
                    "status": "verified",
                    "action": action,
                    "observation_id": obs_id,
                    "active_window": {"title": title, "process": proc_name},
                    "tree": out_text
                }

            fg_hwnd = user32.GetForegroundWindow()
            fg_title = get_window_title(fg_hwnd)
            fg_proc = get_window_process_name(fg_hwnd) or "unknown"
            fg_app = fg_proc[:-4] if fg_proc.endswith(".exe") else fg_proc

            fg_control = None
            try:
                fg_control = auto.GetForegroundControl()
            except Exception:
                pass
            if not fg_control and fg_hwnd:
                try:
                    fg_control = auto.ControlFromHandle(fg_hwnd)
                except Exception:
                    pass
            if not fg_control:
                try:
                    fg_control = auto.GetRootControl()
                except Exception:
                    pass

            if not fg_control:
                return {
                    "status": "failed",
                    "success": False,
                    "message": "No active window or desktop found to observe."
                }

            # Discover currently focused control
            focused_repr = "None"
            try:
                focused_ctrl = auto.GetFocusedControl()
                if focused_ctrl:
                    f_name = focused_ctrl.Name or ""
                    f_type = (focused_ctrl.ControlTypeName or "").replace("Control", "").lower()
                    focused_repr = f"{f_type}: {f_name}".strip()
            except Exception:
                pass

            # Walk and collect interactive elements with deterministic relevance ranking
            collected_elements: List[Tuple[Any, str, str, str]] = []  # (control, eid, type, name)
            eid_counter = 1

            INTERACTIVE_TYPES = {
                "ButtonControl", "EditControl", "ComboBoxControl", "CheckBoxControl",
                "HyperlinkControl", "TabItemControl", "MenuItemControl", "ListItemControl",
                "TreeItemControl", "RadioButtonControl", "DocumentControl"
            }

            def walk_interactive(control, depth=0):
                nonlocal eid_counter
                if depth > 5 or eid_counter > 40:
                    return

                ctype = control.ControlTypeName or ""
                name = (control.Name or "").strip()

                # Value inspection for edits
                val = ""
                if "Edit" in ctype or "Text" in ctype or "Document" in ctype:
                    try:
                        val = control.GetValuePattern().Value
                    except Exception:
                        pass

                is_interactive = ctype in INTERACTIVE_TYPES
                has_meaningful_content = bool(name or val)

                if is_interactive and has_meaningful_content:
                    eid = f"e{eid_counter}"
                    active_cache[eid] = control
                    clean_type = ctype.replace("Control", "").lower()
                    collected_elements.append((control, eid, clean_type, name, val))
                    eid_counter += 1

                for child in control.GetChildren():
                    if eid_counter > 40:
                        break
                    walk_interactive(child, depth + 1)

            walk_interactive(fg_control)

            _observation_store[obs_id] = active_cache
            _element_cache = active_cache

            # Format clean, structured output
            lines = [
                f"OBSERVATION_ID: {obs_id}",
                "ACTIVE WINDOW:",
                f"  Application: {fg_app.title()}",
                f"  Title: {fg_title}",
                f"  Process: {fg_proc}",
                "VISIBLE INTERACTIVE ELEMENTS:"
            ]

            if not collected_elements:
                lines.append("  (No direct interactive controls discovered; window ready for hotkeys or text)")
            else:
                for ctrl, eid, ctype, name, val in collected_elements:
                    val_str = f' value="{val}"' if val else ""
                    lines.append(f"  [{eid}] {ctype}: {name}{val_str}")

            lines.append("FOCUSED ELEMENT:")
            lines.append(f"  {focused_repr}")

            structured_text = "\n".join(lines)
            return {
                "status": "verified",
                "action": action,
                "observation_id": obs_id,
                "active_window": {
                    "application": fg_app,
                    "title": fg_title,
                    "process": fg_proc,
                },
                "interactive_count": len(collected_elements),
                "tree": structured_text
            }

        elif action == "find_element":
            name_query = kwargs.get("name", "").lower().strip()
            matches = []
            curr_elements = _observation_store.get(_current_observation_id, _element_cache)
            for eid, control in curr_elements.items():
                try:
                    if control and name_query in getattr(control, "Name", "").lower():
                        c_type = getattr(control, "ControlTypeName", "").replace("Control", "").lower()
                        matches.append(f"[{eid}] {c_type}: {control.Name}")
                except Exception:
                    pass
            return {
                "status": "verified",
                "action": action,
                "observation_id": _current_observation_id,
                "matches": matches
            }

        elif action == "take_screenshot":
            if not user32 or not gdi32:
                return {"status": "failed", "message": "Screenshot capture only supported on Windows host."}

            try:
                from PIL import ImageGrab
                home = os.path.expanduser('~')
                save_dir = os.path.join(home, "Pictures", "Screenshots")
                try:
                    os.makedirs(save_dir, exist_ok=True)
                except Exception:
                    save_dir = tempfile.gettempdir()

                filename = f"screenshot_{int(time.time())}.png"
                path = os.path.join(save_dir, filename)
                ImageGrab.grab().save(path)
                return {
                    "status": "verified",
                    "action": action,
                    "path": path,
                    "message": f"Screenshot saved to {path}."
                }
            except Exception as e:
                return {"status": "failed", "message": f"Failed to capture screenshot: {e}"}

        return {"status": "failed", "message": "Invalid action"}

    def format_display(self, result: Any) -> str:
        out = result.output if hasattr(result, "output") else result
        if isinstance(out, dict):
            status = out.get('status')
            if status in ['failed', 'error']:
                return f"Screen Observer Error: {out.get('message')}"
            action = out.get('action')
            if action == 'observe_screen':
                return out.get('tree', 'Screen observed.')
            elif action == 'take_screenshot':
                return f"Screenshot saved to: {out.get('path')}"
            elif action == 'find_element':
                matches = out.get('matches', [])
                if not matches:
                    return f"No matching elements found in observation #{out.get('observation_id')}."
                return "Found elements:\n" + "\n".join(matches)
        return str(out)
