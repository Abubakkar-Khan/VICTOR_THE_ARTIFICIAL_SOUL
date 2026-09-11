"""Filesystem Tool for reading local files safely."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from victor.tools.base import BaseTool, PermissionLevel


class FilesystemTool(BaseTool):
    name = "filesystem"
    description = "Read local file contents safely with workspace boundary checks."
    permission = PermissionLevel.CONTROLLED
    slash_command = "/file"
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the local file to read (relative or absolute)."
            },
            "max_lines": {
                "type": "integer",
                "description": "Maximum number of lines to read (default: 200)."
            }
        },
        "required": ["path"]
    }

    def __init__(self, allowed_roots: Optional[List[str]] = None):
        super().__init__()
        self.allowed_roots = [Path(r).resolve() for r in (allowed_roots or ["."])]

    def _is_safe_path(self, target_path: Path) -> bool:
        resolved = target_path.resolve()
        return any(
            resolved == root or root in resolved.parents
            for root in self.allowed_roots
        )

    async def run(self, path: str = "", max_lines: int = 200, **kwargs: Any) -> Dict[str, Any]:
        if not path.strip():
            raise ValueError("No file path specified.")

        file_path = Path(path.strip())
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        if not file_path.is_file():
            raise IsADirectoryError(f"Target is a directory, not a file: {path}")

        if not self._is_safe_path(file_path):
            raise PermissionError(f"Access denied: Path '{path}' is outside allowed directory roots.")

        # Read file with encoding fallback
        encodings = ["utf-8", "latin-1", "cp1252"]
        content = None
        for enc in encodings:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    lines = f.readlines()
                content = lines
                break
            except (UnicodeDecodeError, PermissionError):
                continue

        if content is None:
            raise ValueError(f"Unable to decode text file '{path}' (binary or unsupported encoding).")

        total_lines = len(content)
        truncated = total_lines > max_lines
        selected_lines = content[:max_lines]

        return {
            "path": str(file_path),
            "total_lines": total_lines,
            "read_lines": len(selected_lines),
            "truncated": truncated,
            "content": "".join(selected_lines)
        }

    def intent_patterns(self) -> list[dict]:
        def extract_read(m) -> dict:
            filepath = m.group(1).strip()
            if "." in filepath or "/" in filepath or "\\" in filepath:
                return {"action": "read", "path": filepath}
            return None

        def extract_list(m) -> dict:
            dirpath = m.group(1).strip() or "."
            return {"action": "list", "path": dirpath}

        return [
            {"pattern": r"^(?:read(?:\s+file)?|inspect(?:\s+file)?|view(?:\s+file)?|show(?:\s+file)?)\s+([a-zA-Z0-9_\-\.\/\\~]+)$", "extract": extract_read},
            {"pattern": r"^(?:list\s+files(?:\s+in)?|what\s+files\s+are\s+in|show\s+directory)\s+([a-zA-Z0-9_\-\.\/\\~]*)$", "extract": extract_list}
        ]

    def format_display(self, result) -> str:
        if not result.success:
            return f"I encountered an error executing {self.name}: {result.output}"
        out = result.output
        if isinstance(out, dict):
            path = out.get("path", "")
            lines_count = out.get("total_lines", 0)
            content = out.get("content", "")
            return f"Here is the content of `{path}` ({lines_count} lines):\n\n```\n{content[:1000]}\n```"
        return str(out)

