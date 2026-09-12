"""Application Launcher and Manager Tool for Dexter."""

import os
import shutil
import subprocess
import sys
import ctypes
import re
import urllib.parse
from typing import Any, Dict, List, Optional
from dexter.tools.base import BaseTool, PermissionLevel

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

    CANONICAL_ALIASES = {
        "vs code": "code",
        "vscode": "code",
        "visual studio code": "code",
        "visual studio": "code",
        "vsc": "code",
        "code": "code",
        "google chrome": "chrome",
        "chrome": "chrome",
        "browser": "chrome",
        "google": "chrome",
        "microsoft edge": "msedge",
        "ms edge": "msedge",
        "edge": "msedge",
        "msedge": "msedge",
        "firefox": "firefox",
        "mozilla firefox": "firefox",
        "brave": "brave",
        "brave browser": "brave",
        "file explorer": "explorer",
        "explorer": "explorer",
        "files": "explorer",
        "my computer": "explorer",
        "calc": "calc",
        "calculator": "calc",
        "notepad": "notepad",
        "text editor": "notepad",
        "windows terminal": "wt",
        "terminal": "wt",
        "wt": "wt",
        "command prompt": "cmd",
        "cmd": "cmd",
        "powershell": "powershell",
        "task manager": "taskmgr",
        "taskmgr": "taskmgr",
        "paint": "mspaint",
        "mspaint": "mspaint",
        "snipping tool": "snippingtool",
        "snippingtool": "snippingtool",
        "snip": "snippingtool",
        "word": "winword",
        "winword": "winword",
        "microsoft word": "winword",
        "excel": "excel",
        "microsoft excel": "excel",
        "powerpoint": "powerpnt",
        "ppt": "powerpnt",
        "spotify": "spotify",
    }

    # Known common executable mappings
    COMMON_APPS = {
        "chrome": ["chrome", "google-chrome"],
        "google chrome": ["chrome"],
        "browser": ["chrome", "msedge", "firefox"],
        "edge": ["msedge"],
        "microsoft edge": ["msedge"],
        "firefox": ["firefox"],
        "brave": ["brave"],
        "vscode": ["code"],
        "code": ["code"],
        "vs code": ["code"],
        "visual studio code": ["code"],
        "notepad": ["notepad"],
        "terminal": ["wt", "powershell", "cmd"],
        "windows terminal": ["wt"],
        "powershell": ["powershell"],
        "cmd": ["cmd"],
        "command prompt": ["cmd"],
        "explorer": ["explorer"],
        "file explorer": ["explorer"],
        "calculator": ["calc"],
        "calc": ["calc"],
        "spotify": ["spotify"],
        "paint": ["mspaint"],
        "task manager": ["taskmgr"],
    }

    # URL or special directory aliases
    APP_ALIASES = {
        "gmail": {"url": "https://mail.google.com"},
        "youtube": {"url": "https://youtube.com"},
        "google": {"url": "https://google.com"},
        "downloads": {"path": os.path.join(os.path.expanduser('~'), "Downloads")},
        "downloads folder": {"path": os.path.join(os.path.expanduser('~'), "Downloads")},
        "desktop": {"path": os.path.join(os.path.expanduser('~'), "Desktop")},
        "desktop folder": {"path": os.path.join(os.path.expanduser('~'), "Desktop")},
        "documents": {"path": os.path.join(os.path.expanduser('~'), "Documents")},
        "documents folder": {"path": os.path.join(os.path.expanduser('~'), "Documents")},
        "pictures": {"path": os.path.join(os.path.expanduser('~'), "Pictures")},
        "pictures folder": {"path": os.path.join(os.path.expanduser('~'), "Pictures")},
        "videos": {"path": os.path.join(os.path.expanduser('~'), "Videos")},
        "videos folder": {"path": os.path.join(os.path.expanduser('~'), "Videos")},
        "music": {"path": os.path.join(os.path.expanduser('~'), "Music")},
        "music folder": {"path": os.path.join(os.path.expanduser('~'), "Music")},
        "settings": {"uri": "ms-settings:"},
        "control panel": {"uri": "control"},
    }

    def _resolve_binary(self, app_name: str) -> Optional[str]:
        target = app_name.strip().lower()
        if not target:
            return None

        canonical = self.CANONICAL_ALIASES.get(target, target)

        if sys.platform == "win32":
            import winreg

            # 1. Known standard paths (guaranteed high-quality paths for standard apps)
            standard_paths = {
                "code": [
                    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
                    r"C:\Program Files\Microsoft VS Code\Code.exe",
                    r"C:\Program Files (x86)\Microsoft VS Code\Code.exe",
                ],
                "chrome": [
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
                ],
                "msedge": [
                    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
                ],
                "calc": [
                    r"C:\Windows\System32\calc.exe",
                ],
                "notepad": [
                    r"C:\Windows\System32\notepad.exe",
                ],
                "explorer": [
                    r"C:\Windows\explorer.exe",
                ],
                "cmd": [
                    r"C:\Windows\System32\cmd.exe",
                ],
                "powershell": [
                    r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
                ],
                "wt": [
                    os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WindowsApps\wt.exe"),
                ],
                "mspaint": [
                    r"C:\Windows\System32\mspaint.exe",
                ],
                "taskmgr": [
                    r"C:\Windows\System32\taskmgr.exe",
                ],
            }
            for candidate in standard_paths.get(canonical, []):
                if os.path.exists(candidate):
                    return candidate

            # 2. Windows registry App Paths lookup
            candidates = [f"{canonical}.exe", canonical, f"{target}.exe", target]
            for root in [winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE]:
                for exe in candidates:
                    try:
                        with winreg.OpenKey(root, rf"Software\Microsoft\Windows\CurrentVersion\App Paths\{exe}") as k:
                            val, _ = winreg.QueryValueEx(k, "")
                            if val:
                                val = os.path.expandvars(val.strip('"'))
                                if os.path.exists(val):
                                    return val
                    except Exception:
                        pass

            # 3. Start Menu shortcuts (.lnk exact match first)
            start_dirs = [
                os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
                os.path.expandvars(r"%ALLUSERSPROFILE%\Microsoft\Windows\Start Menu\Programs"),
            ]
            for sdir in start_dirs:
                if not os.path.exists(sdir):
                    continue
                for root_dir, _, files in os.walk(sdir):
                    for f in files:
                        if f.lower().endswith(".lnk"):
                            fname_no_ext = f[:-4].lower()
                            if fname_no_ext in [target, canonical]:
                                return os.path.join(root_dir, f)

            # 4. PATH lookup (preferring .exe, handling .cmd -> parent .exe)
            for c in [f"{canonical}.exe", canonical, f"{target}.exe", target]:
                found = shutil.which(c)
                if found:
                    if found.lower().endswith((".cmd", ".bat")):
                        parent = os.path.dirname(os.path.dirname(found))
                        for exe_name in ["Code.exe", f"{canonical}.exe", f"{target}.exe"]:
                            cand = os.path.join(parent, exe_name)
                            if os.path.exists(cand):
                                return cand
                    else:
                        return found

            # 5. Start Menu substring match (e.g., third-party installed apps like LibreOffice, Slack, etc.)
            for sdir in start_dirs:
                if not os.path.exists(sdir):
                    continue
                for root_dir, _, files in os.walk(sdir):
                    for f in files:
                        if f.lower().endswith(".lnk"):
                            fname_no_ext = f[:-4].lower()
                            if target in fname_no_ext or canonical in fname_no_ext:
                                if not any(bad in fname_no_ext for bad in ["uninstall", "help", "readme", "documentation", "manual"]):
                                    return os.path.join(root_dir, f)

        else:
            # Linux / macOS lookup
            for b in self.COMMON_APPS.get(target, [canonical, target]):
                found = shutil.which(b)
                if found:
                    return found

        return None

    async def run(self, action: str = "open", app_name: str = "", args: str = "", **kwargs: Any) -> Dict[str, Any]:
        if action == "list":
            available = []
            for name in self.COMMON_APPS.keys():
                bin_path = self._resolve_binary(name)
                available.append({"name": name, "installed": bin_path is not None})
            return {
                "action": "list",
                "status": "verified",
                "success": True,
                "applications": available
            }

        elif action == "close":
            target = app_name.strip().lower()
            if not target:
                raise ValueError("Application name is required for 'close' action.")

            if sys.platform == "win32":
                from dexter.tools.verifier import (
                    find_all_windows,
                    ActionVerifier,
                    ActionResultStatus
                )

                canonical = self.CANONICAL_ALIASES.get(target, target)

                # Collect all visible matching windows
                matched_hwnds = []
                for w in find_all_windows(only_visible=True):
                    p_name = w["process_name"].lower()
                    title = w["title"].lower()
                    if (target in p_name or canonical in p_name or target in title or canonical in title):
                        matched_hwnds.append(w["hwnd"])

                if not matched_hwnds:
                    return {
                        "action": "close",
                        "application": app_name,
                        "status": "failed",
                        "success": False,
                        "message": f"No open windows matching '{app_name}' were found on the desktop."
                    }

                # Send WM_CLOSE to matching windows
                for hwnd in matched_hwnds:
                    try:
                        ctypes.windll.user32.PostMessageW(hwnd, 0x0010, 0, 0)
                    except Exception:
                        pass

                # VERIFY that target windows actually closed
                verify_res = await ActionVerifier.verify_app_close(app_name, matched_hwnds, timeout=3.5)
                return {
                    "action": "close",
                    "application": app_name,
                    "status": verify_res["status"],
                    "success": verify_res["success"],
                    "message": verify_res["message"],
                    "verification": verify_res.get("verification", {})
                }
            else:
                return {"action": "close", "status": "failed", "success": False, "message": "Close action is only supported on Windows."}

        elif action == "open":
            target = app_name.strip().lower()
            if not target:
                raise ValueError("Application name is required for 'open' action.")

            from dexter.tools.verifier import ActionVerifier, ActionResultStatus

            canonical = self.CANONICAL_ALIASES.get(target, target)

            # Check special alias (URL, special folder, or settings URI)
            if target in self.APP_ALIASES:
                alias = self.APP_ALIASES[target]
                if "url" in alias:
                    target_url = alias["url"]
                    if sys.platform == "win32":
                        os.startfile(target_url)
                        verify_res = await ActionVerifier.verify_app_launch(
                            app_name=app_name,
                            canonical="chrome",
                            process_hints=["chrome", "msedge", "firefox", "brave"],
                            timeout=5.0
                        )
                        return {
                            "action": "open",
                            "application": app_name,
                            "url": target_url,
                            "status": verify_res["status"],
                            "success": verify_res["success"],
                            "message": f"{app_name.capitalize()} is open in your browser." if verify_res["success"] else verify_res["message"],
                            "verification": verify_res.get("verification", {})
                        }
                    else:
                        subprocess.Popen(["xdg-open", target_url])
                        return {"action": "open", "application": app_name, "status": "executed_unverified", "message": f"Opened {app_name}."}

                elif "path" in alias:
                    target_path = alias["path"]
                    if sys.platform == "win32":
                        os.startfile(target_path)
                        verify_res = await ActionVerifier.verify_app_launch(
                            app_name=app_name,
                            canonical="explorer",
                            process_hints=["explorer"],
                            timeout=5.0
                        )
                        return {
                            "action": "open",
                            "application": app_name,
                            "path": target_path,
                            "status": verify_res["status"],
                            "success": verify_res["success"],
                            "message": f"Opened {app_name} folder." if verify_res["success"] else verify_res["message"],
                            "verification": verify_res.get("verification", {})
                        }
                    else:
                        subprocess.Popen(["xdg-open", target_path])
                        return {"action": "open", "application": app_name, "status": "executed_unverified", "message": f"Opened {app_name} folder."}

                elif "uri" in alias:
                    if sys.platform == "win32":
                        os.startfile(alias["uri"])
                        verify_res = await ActionVerifier.verify_app_launch(
                            app_name=app_name,
                            canonical="systemsettings",
                            process_hints=["systemsettings", "control"],
                            timeout=5.0
                        )
                        return {
                            "action": "open",
                            "application": app_name,
                            "status": verify_res["status"],
                            "success": verify_res["success"],
                            "message": f"Opened Windows {app_name}." if verify_res["success"] else verify_res["message"],
                            "verification": verify_res.get("verification", {})
                        }

            # If user provided a direct URL
            if target.startswith("http://") or target.startswith("https://"):
                if sys.platform == "win32":
                    os.startfile(target)
                    verify_res = await ActionVerifier.verify_app_launch(
                        app_name="Browser",
                        canonical="chrome",
                        process_hints=["chrome", "msedge", "firefox", "brave"],
                        timeout=5.0
                    )
                    return {
                        "action": "open",
                        "application": target,
                        "status": verify_res["status"],
                        "success": verify_res["success"],
                        "message": f"Opened {target} in browser." if verify_res["success"] else verify_res["message"],
                        "verification": verify_res.get("verification", {})
                    }
                return {"action": "open", "application": target, "status": "executed_unverified", "message": f"Opened {target}."}

            bin_path = self._resolve_binary(target)

            if bin_path:
                try:
                    proc_hint = os.path.splitext(os.path.basename(bin_path))[0].lower()
                    if sys.platform == "win32":
                        if args:
                            try:
                                os.startfile(bin_path, arguments=args.strip())
                            except Exception:
                                subprocess.Popen([bin_path, args.strip()], creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
                        else:
                            try:
                                os.startfile(bin_path)
                            except Exception:
                                subprocess.Popen([bin_path], creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)

                        # VERIFY that the application actually produced a visible window on the desktop
                        verify_res = await ActionVerifier.verify_app_launch(
                            app_name=app_name,
                            canonical=canonical,
                            process_hints=[proc_hint],
                            timeout=5.0
                        )
                        return {
                            "action": "open",
                            "application": app_name,
                            "command": bin_path,
                            "status": verify_res["status"],
                            "success": verify_res["success"],
                            "message": verify_res["message"],
                            "verification": verify_res.get("verification", {})
                        }
                    else:
                        launch_args = [bin_path]
                        if args:
                            launch_args.append(args.strip())
                        subprocess.Popen(launch_args, start_new_session=True)
                        return {
                            "action": "open",
                            "application": app_name,
                            "status": "executed_unverified",
                            "message": f"Launched {app_name} on Unix host."
                        }
                except Exception as e:
                    return {
                        "action": "open",
                        "application": app_name,
                        "status": "failed",
                        "success": False,
                        "error": str(e),
                        "message": f"Failed to launch {app_name}: {e}"
                    }

            # Fallback for Windows protocol / app name (e.g. calc:, ms-settings:, or direct shell start)
            if sys.platform == "win32":
                try:
                    os.startfile(target)
                    verify_res = await ActionVerifier.verify_app_launch(
                        app_name=app_name,
                        canonical=canonical,
                        process_hints=[canonical, target],
                        timeout=5.0
                    )
                    return {
                        "action": "open",
                        "application": app_name,
                        "status": verify_res["status"],
                        "success": verify_res["success"],
                        "message": verify_res["message"],
                        "verification": verify_res.get("verification", {})
                    }
                except Exception:
                    try:
                        subprocess.Popen(f'start "" "{target}"', shell=True)
                        verify_res = await ActionVerifier.verify_app_launch(
                            app_name=app_name,
                            canonical=canonical,
                            process_hints=[canonical, target],
                            timeout=5.0
                        )
                        return {
                            "action": "open",
                            "application": app_name,
                            "status": verify_res["status"],
                            "success": verify_res["success"],
                            "message": verify_res["message"],
                            "verification": verify_res.get("verification", {})
                        }
                    except Exception as e:
                        return {
                            "action": "open",
                            "application": app_name,
                            "status": "failed",
                            "success": False,
                            "error": str(e),
                            "message": f"Could not locate or launch application '{app_name}' on your computer. Error: {e}"
                        }

            return {
                "action": "open",
                "application": app_name,
                "status": "failed",
                "success": False,
                "message": f"Application '{app_name}' could not be located on the system."
            }

    def format_display(self, result: Any) -> str:
        out = result.output if hasattr(result, "output") else result
        if isinstance(out, dict):
            status = out.get("status", "")
            action = out.get("action", "")
            msg = out.get("message")

            if msg:
                return msg

            if action == "open":
                app = out.get("application", "Application")
                if status == "verified":
                    return f"{app.capitalize()} is open and visible."
                elif status == "timeout":
                    return f"I couldn't open {app}. Windows did not produce a visible window within 5 seconds."
                elif status == "failed":
                    return f"Failed to open {app}."
                return f"Application status: {status}"

            elif action == "close":
                app = out.get("application", "Application")
                if status == "verified":
                    return f"{app.capitalize()} closed."
                elif status == "failed":
                    return f"{app.capitalize()} is still open."
                return f"Close action status: {status}"

            elif action == "list":
                apps = out.get("applications", [])
                lines = ["Applications:"]
                for app in apps:
                    lines.append(f"- {app['name']}: {'Installed' if app['installed'] else 'Not Installed'}")
                return "\n".join(lines)

        return str(out)

    def intent_patterns(self) -> list[dict]:
        def extract_open(m) -> dict:
            full = m.group(1).strip()
            extra_args = m.group(2).strip() if len(m.groups()) > 1 and m.group(2) else ""

            # Check if user wants to search YouTube
            yt_search = re.search(r'^(?:youtube)\s+(?:and\s+)?(?:search|seacch|serach|look)(?:\s+for)?\s+(.+)$', full, re.I)
            if yt_search:
                q = yt_search.group(1).strip()
                return {"action": "open", "app_name": f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(q)}"}

            # Check if user wants to search in Chrome / Browser / Edge
            browser_search = re.search(r'^(chrome|google\s+chrome|browser|edge|microsoft\s+edge|firefox|brave)\s+(?:and\s+)?(?:search|seacch|serach|look)(?:\s+for)?\s+(.+)$', full, re.I)
            if browser_search:
                q = browser_search.group(2).strip()
                if "youtube" in q.lower():
                    clean_yt = re.sub(r'^(?:and\s+)?(?:go\s+to|open|search(?:\s+for)?)\s*(?:youtube\s*)?', '', q, flags=re.I).strip()
                    return {"action": "open", "app_name": f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(clean_yt)}"}
                return {"action": "open", "app_name": f"https://www.google.com/search?q={urllib.parse.quote_plus(q)}"}

            # App with 'and write/type'
            write_match = re.search(r'^(notepad|word|text\s+editor)\s+and\s+(?:write|type)\s+(.+)$', full, re.I)
            if write_match:
                return {"action": "open", "app_name": write_match.group(1).strip(), "args": write_match.group(2).strip()}

            # Clean trailing 'folder' or leading 'the' for downloads/documents/desktop
            clean_target = re.sub(r'\s+folder$', '', full, flags=re.I).strip()
            clean_target = re.sub(r'^(?:the\s+)', '', clean_target, flags=re.I).strip()

            params = {"action": "open", "app_name": clean_target}
            if extra_args:
                params["args"] = extra_args
            return params

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
            {"pattern": r"^(?:open|launch|start|run|go\s+to)\s+(.+)$", "extract": extract_open},
            {"pattern": r"^(chrome|google\s+chrome|browser|edge|microsoft\s+edge|firefox|brave|vscode|code|vs\s+code|visual\s+studio\s+code|notepad|terminal|windows\s+terminal|powershell|cmd|command\s+prompt|explorer|file\s+explorer|calculator|calc|spotify|gmail|youtube|downloads|desktop|documents|settings|paint|task\s+manager)$", "extract": extract_single},
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
                    
                    # Pretty print app name
                    name_map = {
                        "code": "VS Code",
                        "vscode": "VS Code",
                        "vs code": "VS Code",
                        "visual studio code": "VS Code",
                        "calc": "Calculator",
                        "calculator": "Calculator",
                        "cmd": "Command Prompt",
                        "wt": "Windows Terminal",
                        "terminal": "Terminal",
                        "powershell": "PowerShell",
                        "explorer": "File Explorer",
                        "mspaint": "Paint",
                        "taskmgr": "Task Manager",
                    }
                    display_name = name_map.get(app.lower(), app.title())
                    return f"Done. {display_name} is now open on your screen."
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
