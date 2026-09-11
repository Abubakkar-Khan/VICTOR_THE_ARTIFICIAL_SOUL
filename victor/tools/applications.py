"""Application Launcher and Manager Tool for Victor."""

import os
import shutil
import subprocess
import sys
import ctypes
from typing import Any, Dict, List
from victor.tools.base import BaseTool, PermissionLevel

class ApplicationTool(BaseTool):
    name = "applications"
    description = "Launch, open, list, or close desktop applications."
    permission = PermissionLevel.SAFE
    slash_command = "/app"
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["open", "list", "close"],
                "description": "Action to perform: 'open' an application, 'list' known common apps, or 'close' an app."
            },
            "app_name": {
                "type": "string",
                "description": "Name or alias of the application to open or close."
            },
            "args": {
                "type": "string",
                "description": "Optional file path or URL argument to pass to the application"
            }
        },
        "required": ["action"]
    }

    # Known common executable mappings
    COMMON_APPS = {
        "chrome": ["chrome", "google-chrome"],
        "browser": ["chrome", "msedge", "firefox"],
        "edge": ["msedge"],
        "firefox": ["firefox"],
        "vscode": ["code"],
        "code": ["code"],
        "notepad": ["notepad"],
        "terminal": ["wt", "powershell", "cmd"],
        "powershell": ["powershell"],
        "cmd": ["cmd"],
        "explorer": ["explorer"],
        "calculator": ["calc"],
        "spotify": ["spotify"],
    }

    # URL or special directory aliases
    APP_ALIASES = {
        "gmail": {"url": "https://mail.google.com"},
        "youtube": {"url": "https://youtube.com"},
        "google": {"url": "https://google.com"},
        "downloads": {"path": os.path.join(os.path.expanduser('~'), "Downloads")},
        "desktop": {"path": os.path.join(os.path.expanduser('~'), "Desktop")},
        "documents": {"path": os.path.join(os.path.expanduser('~'), "Documents")},
        "pictures": {"path": os.path.join(os.path.expanduser('~'), "Pictures")},
        "videos": {"path": os.path.join(os.path.expanduser('~'), "Videos")},
        "music": {"path": os.path.join(os.path.expanduser('~'), "Music")},
        "settings": {"uri": "ms-settings:"},
    }

    def _resolve_binary(self, app_name: str) -> Optional[str]:
        target = app_name.strip().lower()

        # 1. Direct which lookup
        for b in self.COMMON_APPS.get(target, [target]):
            found = shutil.which(b)
            if found:
                return found

        # 2. Windows registry App Paths lookup
        if sys.platform == "win32":
            import winreg
            for root in [winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE]:
                for exe in [f"{target}.exe", target]:
                    try:
                        with winreg.OpenKey(root, rf"Software\Microsoft\Windows\CurrentVersion\App Paths\{exe}") as k:
                            val, _ = winreg.QueryValueEx(k, "")
                            if val and os.path.exists(val):
                                return val
                    except Exception:
                        pass

            # 3. Known standard Windows directories
            standard_paths = {
                "chrome": [
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
                ],
                "browser": [
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                ],
                "edge": [
                    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
                ],
                "code": [
                    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
                    r"C:\Program Files\Microsoft VS Code\Code.exe",
                ],
                "vscode": [
                    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
                    r"C:\Program Files\Microsoft VS Code\Code.exe",
                ],
                "notepad": [r"C:\Windows\System32\notepad.exe"],
                "explorer": [r"C:\Windows\explorer.exe"],
                "calculator": [r"C:\Windows\System32\calc.exe"],
            }
            for candidate in standard_paths.get(target, []):
                if os.path.exists(candidate):
                    return candidate

        return None

    async def run(self, action: str = "open", app_name: str = "", args: str = "", **kwargs: Any) -> Dict[str, Any]:
        if action == "list":
            available = []
            for name in self.COMMON_APPS.keys():
                bin_path = self._resolve_binary(name)
                available.append({"name": name, "installed": bin_path is not None})
            return {
                "action": "list",
                "applications": available
            }
            
        elif action == "close":
            target = app_name.strip().lower()
            if not target:
                raise ValueError("Application name is required for 'close' action.")
                
            if sys.platform == "win32":
                EnumWindows = ctypes.windll.user32.EnumWindows
                EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
                GetWindowText = ctypes.windll.user32.GetWindowTextW
                GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
                IsWindowVisible = ctypes.windll.user32.IsWindowVisible
                SendMessage = ctypes.windll.user32.SendMessageW
                WM_CLOSE = 0x0010
                
                closed_count = 0
                
                def foreach_window(hwnd, lParam):
                    nonlocal closed_count
                    if IsWindowVisible(hwnd):
                        length = GetWindowTextLength(hwnd)
                        if length > 0:
                            buff = ctypes.create_unicode_buffer(length + 1)
                            GetWindowText(hwnd, buff, length + 1)
                            title = buff.value.lower()
                            if target in title:
                                SendMessage(hwnd, WM_CLOSE, 0, 0)
                                closed_count += 1
                    return True
                    
                EnumWindows(EnumWindowsProc(foreach_window), 0)
                
                if closed_count > 0:
                    return {"action": "close", "status": "success", "message": f"Sent close signal to {closed_count} windows matching '{app_name}'."}
                else:
                    return {"action": "close", "status": "not_found", "message": f"No visible windows found matching '{app_name}'."}
            else:
                return {"action": "close", "status": "error", "message": "Close action is only supported on Windows."}

        elif action == "open":
            target = app_name.strip().lower()
            if not target:
                raise ValueError("Application name is required for 'open' action.")

            # Check special alias (URL, special folder, or settings URI)
            if target in self.APP_ALIASES:
                alias = self.APP_ALIASES[target]
                if "url" in alias:
                    target_url = alias["url"]
                    if sys.platform == "win32":
                        os.startfile(target_url)
                    else:
                        subprocess.Popen(["xdg-open", target_url])
                    return {"action": "open", "application": app_name, "status": "launched", "message": f"Opened {app_name} ({target_url})."}
                elif "path" in alias:
                    target_path = alias["path"]
                    if sys.platform == "win32":
                        os.startfile(target_path)
                    else:
                        subprocess.Popen(["xdg-open", target_path])
                    return {"action": "open", "application": app_name, "status": "launched", "message": f"Opened {app_name} folder ({target_path})."}
                elif "uri" in alias:
                    if sys.platform == "win32":
                        os.startfile(alias["uri"])
                    return {"action": "open", "application": app_name, "status": "launched", "message": f"Opened Windows {app_name}."}

            # If user provided a direct URL as app_name or args
            if target.startswith("http://") or target.startswith("https://"):
                if sys.platform == "win32":
                    os.startfile(target)
                return {"action": "open", "application": target, "status": "launched", "message": f"Opened URL {target} in default browser."}

            bin_path = self._resolve_binary(target)
            
            if bin_path:
                launch_args = [bin_path]
                if args:
                    launch_args.append(args.strip())
                try:
                    if sys.platform == "win32":
                        # Launch in foreground where user sees the window
                        if not args:
                            try:
                                os.startfile(bin_path)
                            except Exception:
                                subprocess.Popen(launch_args, shell=False)
                        else:
                            subprocess.Popen(launch_args, shell=False)
                    else:
                        subprocess.Popen(launch_args, start_new_session=True)
                    return {
                        "action": "open",
                        "application": app_name,
                        "command": bin_path,
                        "args": args,
                        "status": "launched",
                        "message": f"Successfully launched {app_name}.",
                    }
                except Exception as e:
                    # Fallback to os.startfile on Windows
                    if sys.platform == "win32":
                        try:
                            os.startfile(bin_path)
                            return {"action": "open", "application": app_name, "status": "launched", "message": f"Launched {app_name} via Windows shell."}
                        except Exception:
                            pass
                    return {"action": "open", "application": app_name, "status": "error", "error": str(e)}

            # Fallback for Windows protocol / app name
            if sys.platform == "win32":
                try:
                    os.startfile(target)
                    return {"action": "open", "application": app_name, "status": "launched", "message": f"Opened {app_name} via Windows shell."}
                except Exception as e:
                    raise FileNotFoundError(f"Could not locate or launch application '{app_name}' on your computer. Error: {e}")

            raise FileNotFoundError(f"Application '{app_name}' could not be located on the system.")

    def intent_patterns(self) -> list[dict]:
        import re
        import urllib.parse

        def extract_open(m) -> dict:
            app_target = m.group(1).strip().lower()
            extra_args = m.group(2).strip() if len(m.groups()) > 1 else ""

            # Check if user wants to search YouTube
            if "youtube" in app_target:
                if extra_args:
                    clean_q = re.sub(r'^(?:and\s+)?search(?:\s+for)?\s*', '', extra_args, flags=re.I).strip()
                    if clean_q:
                        return {"action": "open", "app_name": f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(clean_q)}"}
                return {"action": "open", "app_name": "youtube"}

            # Check if user wants to search in Chrome / Browser / Edge
            if app_target in ["chrome", "google chrome", "browser", "edge", "firefox"]:
                if extra_args:
                    if "youtube" in extra_args.lower():
                        clean_yt = re.sub(r'^(?:and\s+)?(?:go\s+to|open|search(?:\s+for)?)\s*(?:youtube\s*)?', '', extra_args, flags=re.I).strip()
                        if clean_yt:
                            return {"action": "open", "app_name": f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(clean_yt)}"}
                        return {"action": "open", "app_name": "youtube"}
                    clean_q = re.sub(r'^(?:and\s+)?(?:search|seacch|serach|look)(?:\s+for)?\s*', '', extra_args, flags=re.I).strip()
                    if clean_q:
                        return {"action": "open", "app_name": f"https://www.google.com/search?q={urllib.parse.quote_plus(clean_q)}"}

            if "downloads" in app_target:
                return {"action": "open", "app_name": "downloads"}
            if "gmail" in app_target:
                return {"action": "open", "app_name": "gmail"}
            if "settings" in app_target:
                return {"action": "open", "app_name": "settings"}

            return {"action": "open", "app_name": app_target, "args": extra_args}

        def extract_single(m) -> dict:
            app_target = m.group(1).strip().lower()
            if app_target == "calc":
                app_target = "calculator"
            return {"action": "open", "app_name": app_target}

        def extract_youtube_search(m) -> dict:
            query = m.group(1).strip()
            return {"action": "open", "app_name": f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(query)}"}

        def extract_google_search(m) -> dict:
            query = m.group(1).strip()
            return {"action": "open", "app_name": f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}"}

        def extract_close(m) -> dict:
            app_target = m.group(1).strip()
            return {"action": "close", "app_name": app_target}

        return [
            {"pattern": r"^(?:open|launch|start|run|go\s+to)\s+(chrome|google\s+chrome|browser|edge|firefox|vscode|code|vs\s+code|notepad|terminal|powershell|cmd|explorer|calculator|calc|spotify|gmail|youtube|downloads(?:\s+folder)?|desktop|documents|settings)\b\s*(.*)$", "extract": extract_open},
            {"pattern": r"^(chrome|google\s+chrome|browser|edge|firefox|vscode|code|notepad|terminal|calculator|calc|spotify|gmail|youtube|downloads|desktop|documents|settings)$", "extract": extract_single},
            {"pattern": r"^(?:search\s+youtube\s+for|look\s+up\s+on\s+youtube|open\s+youtube\s+and\s+search\s+for)\s+(.+)$", "extract": extract_youtube_search},
            {"pattern": r"^(?:search\s+(?:google|web|the\s+web)\s+for)\s+(.+)$", "extract": extract_google_search},
            {"pattern": r"^(?:close|quit|exit|kill)\s+(.+)$", "extract": extract_close}
        ]

    def format_display(self, result) -> str:
        if not result.success:
            return f"I could not complete the action: {result.error or result.output}"
        out = result.output
        if isinstance(out, dict):
            action = out.get("action")
            if action == "open":
                app = out.get("application", "")
                status = out.get("status", "")
                if status == "launched":
                    if "youtube.com/results" in app:
                        return "Done. I opened YouTube with your search in the browser."
                    elif "google.com/search" in app:
                        return "Done. I opened Google with your search in the browser."
                    elif "http" in app:
                        return f"Done. I opened {app} in your browser."
                    return f"Done. {app.capitalize()} is now open on your screen."
                return out.get("message", f"Application status: {status}")
            elif action == "close":
                return out.get("message", "Executed close action.")
            elif action == "list":
                apps = out.get("applications", [])
                msg = "Applications:\n"
                for app in apps:
                    msg += f"- {app['name']}: {'Installed' if app['installed'] else 'Not Installed'}\n"
                return msg
        return str(out)
