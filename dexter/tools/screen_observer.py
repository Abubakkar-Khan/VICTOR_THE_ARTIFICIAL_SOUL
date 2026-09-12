import ctypes
import os
import tempfile
from typing import Any, Dict
from dexter.tools.base import BaseTool, PermissionLevel

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

try:
    import uiautomation as auto
    HAS_UIAUTOMATION = True
except ImportError:
    HAS_UIAUTOMATION = False

_element_cache: Dict[str, Any] = {}

class ScreenObserverTool(BaseTool):
    name = "screen_observer"
    description = "Screen understanding via Windows UI Automation accessibility tree and screenshot."
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
                "description": "Name of the element to find (for find_element)."
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
        action = kwargs.get("action")
        
        if action == "observe_screen":
            if not HAS_UIAUTOMATION:
                hwnd = user32.GetForegroundWindow()
                length = user32.GetWindowTextLengthW(hwnd)
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                return {"status": "success", "action": action, "tree": f"[e1] {buf.value} (window)\n  (uiautomation not installed)"}
            
            global _element_cache
            _element_cache.clear()
            
            fg_window = auto.GetForegroundControl()
            if not fg_window:
                hwnd = user32.GetForegroundWindow()
                if hwnd:
                    try:
                        fg_window = auto.ControlFromHandle(hwnd)
                    except Exception:
                        pass
                if not fg_window:
                    try:
                        fg_window = auto.GetRootControl()
                    except Exception:
                        pass
            if not fg_window:
                return {"status": "error", "message": "No active window or desktop found to observe."}
                
            tree_lines = []
            element_id_counter = 1
            
            def walk(control, depth=0):
                nonlocal element_id_counter
                if depth > 4 or element_id_counter > 50:
                    return
                
                eid = f"e{element_id_counter}"
                _element_cache[eid] = control
                
                ctype = control.ControlTypeName
                name = control.Name
                
                line = f"{'  ' * depth}[{eid}] {name} ({ctype})"
                # For edit controls try to get value
                if 'Edit' in ctype or 'Text' in ctype:
                    try:
                        val = control.GetValuePattern().Value
                        if val:
                            line += f' value="{val}"'
                    except:
                        pass
                
                tree_lines.append(line)
                element_id_counter += 1
                
                for child in control.GetChildren():
                    if element_id_counter > 50:
                        break
                    walk(child, depth + 1)
            
            walk(fg_window)
            return {"status": "success", "action": action, "tree": "\n".join(tree_lines)}
            
        elif action == "find_element":
            name_query = kwargs.get("name", "").lower()
            matches = []
            for eid, control in _element_cache.items():
                try:
                    if name_query in control.Name.lower():
                        matches.append(f"[{eid}] {control.Name} ({control.ControlTypeName})")
                except:
                    pass
            return {"status": "success", "action": action, "matches": matches}
            
        elif action == "take_screenshot":
            # Using ctypes to take screenshot
            SRCCOPY = 0x00CC0020
            width = user32.GetSystemMetrics(0)
            height = user32.GetSystemMetrics(1)
            
            hwnd = user32.GetDesktopWindow()
            hdc = user32.GetWindowDC(hwnd)
            mfcDC = gdi32.CreateCompatibleDC(hdc)
            saveBitMap = gdi32.CreateCompatibleBitmap(hdc, width, height)
            gdi32.SelectObject(mfcDC, saveBitMap)
            gdi32.BitBlt(mfcDC, 0, 0, width, height, hdc, 0, 0, SRCCOPY)
            
            # We need to save the bitmap. Python ctypes doesn't have a built-in save to PNG.
            # Usually we'd use PIL.ImageGrab. Since we're restricted to ctypes, we'll just write a basic BMP or use PIL if we can.
            # Let's try to use PIL since it's standard for this.
            try:
                import time
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
            except Exception as e:
                return {"status": "error", "message": f"Failed to capture screenshot: {e}"}
            finally:
                gdi32.DeleteObject(saveBitMap)
                gdi32.DeleteDC(mfcDC)
                user32.ReleaseDC(hwnd, hdc)
                
            return {"status": "success", "action": action, "path": path}
            
        return {"status": "error", "message": "Invalid action"}

    def format_display(self, result: Any) -> str:
        out = result.output if hasattr(result, "output") else result
        if isinstance(out, dict):
            status = out.get('status')
            if status == 'error':
                return f"Screen Observer Error: {out.get('message')}"
            action = out.get('action')
            if action == 'observe_screen':
                return f"Screen Tree:\n{out.get('tree')}"
            elif action == 'take_screenshot':
                return f"Screenshot saved to: {out.get('path')}"
            elif action == 'find_element':
                matches = out.get('matches', [])
                if not matches:
                    return "No matching elements found on screen."
                return "Found elements:\n" + "\n".join(matches)
        return str(out)
