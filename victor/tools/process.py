"""Process Management Tool for Victor (OpenClaw standard)."""

import csv
import io
import os
import re
import subprocess
import sys
from typing import Any, Dict, List, Optional
from victor.tools.base import BaseTool, PermissionLevel


class ProcessTool(BaseTool):
    name = "process"
    description = "Inspect and manage running system processes: list active processes, check status, or kill by name/PID (OpenClaw standard)."
    permission = PermissionLevel.CONTROLLED
    slash_command = "/process"
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["list", "kill", "status"],
                "description": "The process action to perform."
            },
            "target": {
                "type": "string",
                "description": "Process name (e.g. 'chrome.exe', 'notepad') or numeric PID."
            },
            "filter": {
                "type": "string",
                "description": "Filter substring for listing processes."
            }
        },
        "required": ["action"]
    }

    def _list_processes_windows(self, filter_term: str = "") -> List[Dict[str, Any]]:
        res = subprocess.run(
            ["tasklist", "/fo", "csv", "/nh"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        reader = csv.reader(io.StringIO(res.stdout))
        procs = []
        filter_lower = filter_term.lower().strip()
        seen = set()

        for row in reader:
            if not row or len(row) < 5:
                continue
            name, pid, session_name, session_num, mem = row[0], row[1], row[2], row[3], row[4]
            if filter_lower and filter_lower not in name.lower() and filter_lower != pid:
                continue
            # Keep unique or top
            procs.append({
                "name": name,
                "pid": pid,
                "memory": mem
            })
        return procs

    def _list_processes_unix(self, filter_term: str = "") -> List[Dict[str, Any]]:
        res = subprocess.run(
            ["ps", "-eo", "pid,comm,%mem"],
            capture_output=True,
            text=True,
            errors="replace"
        )
        procs = []
        filter_lower = filter_term.lower().strip()
        lines = res.stdout.strip().split("\n")
        for line in lines[1:]:
            parts = line.split(None, 2)
            if len(parts) >= 2:
                pid, comm = parts[0], parts[1]
                if filter_lower and filter_lower not in comm.lower() and filter_lower != pid:
                    continue
                procs.append({"name": comm, "pid": pid, "memory": parts[2] if len(parts) > 2 else ""})
        return procs

    async def run(self, action: str = "list", target: Optional[str] = None, filter: Optional[str] = None, **kwargs: Any) -> Dict[str, Any]:
        act = action.strip().lower() if action else "list"
        query = (target or filter or "").strip()

        if act.startswith("kill "):
            parts = act.split(maxsplit=1)
            act = parts[0]
            query = parts[1].strip()
        elif act.startswith("status "):
            parts = act.split(maxsplit=1)
            act = parts[0]
            query = parts[1].strip()
        elif act.startswith("list "):
            parts = act.split(maxsplit=1)
            act = parts[0]
            query = parts[1].strip()
        elif act not in ["list", "kill", "status"]:
            query = act
            act = "list"

        if act == "list":
            if sys.platform == "win32":
                procs = self._list_processes_windows(query)
            else:
                procs = self._list_processes_unix(query)
            return {
                "action": "list",
                "filter": query,
                "count": len(procs),
                "processes": procs[:30]
            }

        elif act == "status":
            if not query:
                raise ValueError("Target process name or PID is required for status check.")
            if sys.platform == "win32":
                procs = self._list_processes_windows(query)
            else:
                procs = self._list_processes_unix(query)
            is_running = len(procs) > 0
            return {
                "action": "status",
                "target": query,
                "running": is_running,
                "instances": len(procs),
                "matches": procs[:10]
            }

        elif act == "kill":
            if not query:
                raise ValueError("Target process name or PID is required to terminate.")
            
            if sys.platform == "win32":
                # Check if query is PID
                if query.isdigit():
                    cmd = ["taskkill", "/F", "/PID", query]
                else:
                    target_name = query if query.lower().endswith(".exe") else f"{query}.exe"
                    cmd = ["taskkill", "/F", "/IM", target_name]
                
                res = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
                success = res.returncode == 0
                msg = res.stdout.strip() or res.stderr.strip()
                return {
                    "action": "kill",
                    "target": query,
                    "status": "terminated" if success else "failed",
                    "message": msg
                }
            else:
                cmd = ["kill", "-9", query] if query.isdigit() else ["pkill", "-f", query]
                res = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
                success = res.returncode == 0
                return {
                    "action": "kill",
                    "target": query,
                    "status": "terminated" if success else "failed",
                    "message": res.stdout.strip() or res.stderr.strip()
                }

        raise ValueError(f"Unknown process action: '{action}'")

    def intent_patterns(self) -> list[dict]:
        return [
            {"pattern": r"^(?:list\s+processes|running\s+processes|show\s+processes|ps|get-process)$", "extract": {"action": "list"}},
            {"pattern": r"^(?:list\s+processes\s+matching|find\s+process)\s+(.+)$", "extract": lambda m: {"action": "list", "filter": m.group(1).strip()}},
            {"pattern": r"^(?:kill\s+process|terminate\s+process|end\s+task|stop\s+process|kill)\s+(.+)$", "extract": lambda m: {"action": "kill", "target": m.group(1).strip()}},
            {"pattern": r"^(?:is\s+process\s+running|check\s+process|status\s+of\s+process)\s+(.+)$", "extract": lambda m: {"action": "status", "target": m.group(1).strip()}}
        ]

    def format_display(self, result: Any) -> str:
        if not result.success:
            return f"Process operation error: {result.error or result.output}"
        out = result.output
        if isinstance(out, dict):
            act = out.get("action")
            if act == "list":
                procs = out.get("processes", [])
                filt = out.get("filter", "")
                header = f"Active processes ({out.get('count', len(procs))}"
                if filt:
                    header += f" matching '{filt}'"
                header += "):\n"
                lines = [f"- {p['name']} (PID: {p['pid']}, Mem: {p.get('memory', 'N/A')})" for p in procs[:20]]
                return header + "\n".join(lines)
            elif act == "status":
                target = out.get("target")
                running = out.get("running")
                instances = out.get("instances", 0)
                if running:
                    return f"Process '{target}' is RUNNING with {instances} active instance(s)."
                return f"Process '{target}' is NOT running."
            elif act == "kill":
                return out.get("message", f"Process kill action executed on '{out.get('target')}'.")
        return str(out)
