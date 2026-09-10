"""Shell Command Execution Tool for Victor (DANGEROUS permission)."""

import asyncio
import subprocess
from typing import Any, Dict
from victor.tools.base import BaseTool, PermissionLevel


class ShellTool(BaseTool):
    name = "shell"
    description = "Execute a local terminal/shell command (DANGEROUS - Requires explicit permission)."
    permission = PermissionLevel.DANGEROUS
    slash_command = "/shell"
    parameters = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "Shell command to execute."
            },
            "timeout_seconds": {
                "type": "integer",
                "description": "Execution timeout in seconds (default: 30)."
            }
        },
        "required": ["command"]
    }

    async def run(self, command: str = "", timeout_seconds: int = 30, **kwargs: Any) -> Dict[str, Any]:
        cmd = command.strip()
        if not cmd:
            raise ValueError("No command specified.")

        # Run process asynchronously with timeout
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(),
                timeout=float(timeout_seconds)
            )
        except asyncio.TimeoutError:
            try:
                proc.kill()
            except Exception:
                pass
            raise TimeoutError(f"Command timed out after {timeout_seconds} seconds.")

        stdout_text = stdout_bytes.decode(errors="replace").strip()
        stderr_text = stderr_bytes.decode(errors="replace").strip()

        return {
            "command": cmd,
            "exit_code": proc.returncode,
            "stdout": stdout_text,
            "stderr": stderr_text,
            "success": proc.returncode == 0
        }
