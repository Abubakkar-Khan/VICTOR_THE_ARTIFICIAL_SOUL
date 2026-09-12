import ctypes
import ctypes.wintypes
from typing import Any
from dexter.tools.base import BaseTool, PermissionLevel

user32 = ctypes.windll.user32

SW_MINIMIZE = 6
SW_MAXIMIZE = 3
SW_RESTORE = 9
WM_CLOSE = 0x0010

def _get_window_title(hwnd):
    length = user32.GetWindowTextLengthW(hwnd)
    if length == 0:
        return ""
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    return buf.value

def _is_window_visible(hwnd):
    return user32.IsWindowVisible(hwnd)

def _list_windows():
    windows = []
    fg_hwnd = user32.GetForegroundWindow()
    
    def enum_windows_proc(hwnd, lParam):
        if _is_window_visible(hwnd):
            title = _get_window_title(hwnd)
            if title:
                windows.append({
                    "hwnd": hwnd,
                    "title": title,
                    "is_foreground": hwnd == fg_hwnd
                })
        return True
    
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    user32.EnumWindows(EnumWindowsProc(enum_windows_proc), 0)
    return windows

def _find_window(title_query):
    query = title_query.lower().strip()
    if query in ["this", "this window", "current window", "active window", "it", ""]:
        fg_hwnd = user32.GetForegroundWindow()
        if fg_hwnd:
            length = user32.GetWindowTextLengthW(fg_hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(fg_hwnd, buff, length + 1)
            return {"hwnd": fg_hwnd, "title": buff.value, "is_foreground": True}

    windows = _list_windows()
    
    # Priority 1: Exact match
    for w in windows:
        if w['title'].lower() == query:
            return w
    
    # Priority 2: Starts with
    for w in windows:
        if w['title'].lower().startswith(query):
            return w
            
    # Priority 3: Contains
    for w in windows:
        if query in w['title'].lower():
            return w
            
    return None

class WindowManagerTool(BaseTool):
    name = "window_manager"
    description = "Window management tool using ctypes to list, focus, minimize, maximize, restore, and close windows."
    permission = PermissionLevel.CONTROLLED
    slash_command = "/window"
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["list_windows", "focus_window", "minimize", "maximize", "restore", "close_window"],
                "description": "Action to perform on windows."
            },
            "title": {
                "type": "string",
                "description": "Title of the window to target (required for most actions except list_windows)."
            }
        },
        "required": ["action"]
    }

    def intent_patterns(self) -> list[dict]:
        return [
            {"pattern": r'^(?:list windows|what windows are open|show windows)$', "extract": {"action": "list_windows"}},
            {"pattern": r'^minimize\s+(.+)$', "extract": lambda m: {"action": "minimize", "title": m.group(1).strip()}},
            {"pattern": r'^maximize\s+(.+)$', "extract": lambda m: {"action": "maximize", "title": m.group(1).strip()}},
            {"pattern": r'^close\s+(.+)$', "extract": lambda m: {"action": "close_window", "title": m.group(1).strip()}},
            {"pattern": r'^(?:switch to|focus)\s+(.+)$', "extract": lambda m: {"action": "focus_window", "title": m.group(1).strip()}},
            {"pattern": r'^restore\s+(.+)$', "extract": lambda m: {"action": "restore", "title": m.group(1).strip()}}
        ]

    async def run(self, **kwargs) -> Any:
        action = kwargs.get("action") or "list_windows"
        action = action.strip()
        title = kwargs.get("title", "")

        # Handle composite action strings from slash commands e.g. /window minimize chrome
        if " " in action:
            parts = action.split(maxsplit=1)
            verb = parts[0].lower()
            rest = parts[1].strip()
            verb_map = {
                "list": "list_windows",
                "focus": "focus_window",
                "switch": "focus_window",
                "minimize": "minimize",
                "maximize": "maximize",
                "restore": "restore",
                "close": "close_window",
            }
            if verb in verb_map:
                action = verb_map[verb]
                if not title:
                    title = rest

        if action in ["list", "list_windows"]:
            windows = _list_windows()
            return {"status": "success", "action": "list_windows", "windows": windows}
            
        if not title:
            return {"status": "error", "message": "Window title required"}
            
        target = _find_window(title)
        if not target:
            return {"status": "error", "message": f"Window matching '{title}' not found"}
            
        hwnd = target['hwnd']
        matched_title = target['title']
        
        if action == "focus_window":
            user32.AllowSetForegroundWindow(-1)
            if user32.IsIconic(hwnd):
                user32.ShowWindow(hwnd, SW_RESTORE)
            user32.SetForegroundWindow(hwnd)
            return {"status": "success", "action": action, "window": matched_title}
            
        elif action == "minimize":
            user32.ShowWindow(hwnd, SW_MINIMIZE)
            return {"status": "success", "action": action, "window": matched_title}
            
        elif action == "maximize":
            user32.ShowWindow(hwnd, SW_MAXIMIZE)
            return {"status": "success", "action": action, "window": matched_title}
            
        elif action == "restore":
            user32.ShowWindow(hwnd, SW_RESTORE)
            return {"status": "success", "action": action, "window": matched_title}
            
        elif action == "close_window":
            user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
            return {"status": "success", "action": action, "window": matched_title}
            
        return {"status": "error", "message": "Invalid action"}

    def format_display(self, result: Any) -> str:
        out = result.output if hasattr(result, "output") else result
        if isinstance(out, dict):
            status = out.get('status')
            if status == 'error':
                return f"Window Error: {out.get('message')}"
                
            action = out.get('action')
            if action == 'list_windows':
                wins = out.get('windows', [])
                lines = [f"{'[Active] ' if w['is_foreground'] else '• '}{w['title']}" for w in wins[:15]]
                return f"Open Windows ({len(wins)}):\n" + "\n".join(lines)
            else:
                return f"Window action '{action}' completed on \"{out.get('window')}\"."
        return str(out)
