"""Exec / Shell Command Execution Tool for Victor (OpenClaw standard)."""

import asyncio
import os
import sys
from typing import Any, Dict, Optional
from dexter.tools.base import BaseTool, PermissionLevel


class ExecTool(BaseTool):
    name = "exec"
    description = "Execute a local shell / terminal command with timeout and output capture (OpenClaw runtime standard)."
    permission = PermissionLevel.DANGEROUS
    slash_command = "/exec"
    parameters = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "Shell command to execute."
            },
            "workdir": {
                "type": "string",
                "description": "Working directory for the command (default: current workspace)."
            },
            "timeout_seconds": {
                "type": "integer",
                "description": "Execution timeout in seconds (default: 30)."
            }
        },
        "required": ["command"]
    }

    async def run(self, command: str = "", workdir: Optional[str] = None, timeout_seconds: int = 30, **kwargs: Any) -> Dict[str, Any]:
        cmd = command.strip()
        if not cmd:
            raise ValueError("No command specified.")

        cwd = workdir.strip() if workdir else os.getcwd()
        if cwd and not os.path.exists(cwd):
            raise FileNotFoundError(f"Working directory does not exist: {cwd}")

        # On Windows use powershell or cmd
        if sys.platform == "win32":
            shell_cmd = f'powershell.exe -NoProfile -NonInteractive -Command "{cmd}"'
        else:
            shell_cmd = cmd

        proc = await asyncio.create_subprocess_shell(
            shell_cmd,
            cwd=cwd,
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
            "cwd": cwd,
            "exit_code": proc.returncode,
            "stdout": stdout_text,
            "stderr": stderr_text,
            "success": proc.returncode == 0
        }

    def intent_patterns(self) -> list[dict]:
        return [
            {"pattern": r"^(?:exec|execute|run\s+command|run\s+in\s+terminal|terminal|powershell|cmd|shell)\s+(.+)$", "extract": lambda m: {"command": m.group(1).strip()}}
        ]

    def format_display(self, result: Any) -> str:
        if not result.success:
            return f"Command execution error: {result.error or result.output}"
        out = result.output
        if isinstance(out, dict):
            cmd = out.get("command", "")
            code = out.get("exit_code", 0)
            stdout = out.get("stdout", "")
            stderr = out.get("stderr", "")
            lines = [f"$ {cmd}"]
            if stdout:
                lines.append(stdout[:2500])
            if stderr:
                lines.append(f"Stderr:\n{stderr[:1000]}")
            if code != 0:
                lines.append(f"(exit code: {code})")
            elif not stdout and not stderr:
                lines.append("(command completed with no output)")
            return "\n".join(lines)
        return str(out)


class ShellTool(ExecTool):
    """Backwards-compatible alias for ShellTool referencing ExecTool."""
    name = "shell"
    slash_command = "/shell"
