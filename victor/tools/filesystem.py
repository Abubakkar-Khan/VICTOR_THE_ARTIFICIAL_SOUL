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
