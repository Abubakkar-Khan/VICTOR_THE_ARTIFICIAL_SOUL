"""Application Launcher and Manager Tool for Victor."""

import os
import shutil
import subprocess
import sys
from typing import Any, Dict, List
from victor.tools.base import BaseTool, PermissionLevel


class ApplicationTool(BaseTool):
    name = "applications"
    description = "Launch, open, or list desktop applications (e.g. Chrome, VS Code, Notepad, Terminal, Explorer)."
    permission = PermissionLevel.SAFE
    slash_command = "/open"
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["open", "list"],
                "description": "Action to perform: 'open' an application or 'list' known common apps."
            },
            "app_name": {
                "type": "string",
                "description": "Name or alias of the application to open, e.g. 'chrome', 'code', 'notepad', 'terminal', 'explorer'"
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

    async def run(self, action: str = "open", app_name: str = "", args: str = "", **kwargs: Any) -> Dict[str, Any]:
        if action == "list":
            available = []
            for name, binaries in self.COMMON_APPS.items():
                found = any(shutil.which(b) for b in binaries)
                available.append({"name": name, "installed": found})
            return {
                "action": "list",
                "applications": available
            }

        target = app_name.strip().lower()
        if not target:
            raise ValueError("Application name is required for 'open' action.")

        binaries = self.COMMON_APPS.get(target, [target])
        cmd_to_run = None

        for b in binaries:
            if shutil.which(b):
                cmd_to_run = b
                break

        # Fallback to direct name on Windows
        if not cmd_to_run and sys.platform == "win32":
            cmd_to_run = target

        if not cmd_to_run:
            raise FileNotFoundError(f"Application '{app_name}' could not be located on the system PATH.")

        launch_args = [cmd_to_run]
        if args:
            launch_args.append(args.strip())

        try:
            if sys.platform == "win32":
                # Detached background process
                DETACHED_PROCESS = 0x00000008
                CREATE_NEW_PROCESS_GROUP = 0x00000200
                subprocess.Popen(
                    launch_args,
                    creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
                    shell=True,
                )
            else:
                subprocess.Popen(launch_args, start_new_session=True)

            return {
                "action": "open",
                "application": app_name,
                "command": cmd_to_run,
                "args": args,
                "status": "launched",
                "message": f"Successfully launched {app_name}.",
            }
        except Exception as e:
            return {
                "action": "open",
                "application": app_name,
                "status": "error",
                "error": str(e),
            }
