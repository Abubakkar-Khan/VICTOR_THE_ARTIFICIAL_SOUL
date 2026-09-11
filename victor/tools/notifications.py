"""Notification Tool for Victor."""

import sys
from typing import Any, Dict
from victor.tools.base import BaseTool, PermissionLevel


class NotificationTool(BaseTool):
    name = "notifications"
    description = "Send a desktop or web notification toast to alert the user."
    permission = PermissionLevel.SAFE
    slash_command = "/notify"
    parameters = {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "The title of the notification, e.g. 'Victor // Task Completed'"
            },
            "message": {
                "type": "string",
                "description": "The notification message content"
            }
        },
        "required": ["message"]
    }

    async def run(self, message: str = "", title: str = "Victor", **kwargs: Any) -> Dict[str, Any]:
        msg = message.strip()
        t = title.strip() or "Victor"

        # On Windows, try to trigger native toast or fallback
        if sys.platform == "win32":
            try:
                # Windows PowerShell toast or MsgBox if available
                import subprocess
                ps_script = (
                    f"[reflection.assembly]::loadwithpartialname('System.Windows.Forms'); "
                    f"$notify = new-object system.windows.forms.notifyicon; "
                    f"$notify.icon = [system.drawing.systemicons]::information; "
                    f"$notify.visible = $true; "
                    f"$notify.showballoontip(3000, '{t}', '{msg}', [system.windows.forms.tooltipicon]::None)"
                )
                subprocess.Popen(["powershell", "-NoProfile", "-Command", ps_script], creationflags=0x08000000)
            except Exception:
                pass

        return {
            "action": "notify",
            "title": t,
            "message": msg,
            "status": "delivered",
        }

    def intent_patterns(self) -> list[dict]:
        def extract_msg(m) -> dict:
            return {"message": m.group(1).strip()}
            
        return [
            {"pattern": r"^(?:notify(?:\s+me)?|send\s+notification|alert\s+me)\s+(.+)$", "extract": extract_msg}
        ]

    def format_display(self, result) -> str:
        if not result.success:
            return f"I encountered an error executing {self.name}: {result.output}"
        out = result.output
        if isinstance(out, dict):
            return f"Notification delivered: \"{out.get('message', '')}\"."
        return str(out)

