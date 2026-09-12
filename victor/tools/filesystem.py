"""Filesystem Tool for reading, listing, searching, and managing local files."""

import os
import re
import sys
import shutil
import fnmatch
from pathlib import Path
from typing import Any, Dict, List, Optional
from victor.tools.base import BaseTool, PermissionLevel

class FilesystemTool(BaseTool):
    name = "filesystem"
    description = "Read local file contents, list directories, search files, open files/folders, and create folders."
    permission = PermissionLevel.CONTROLLED
    slash_command = "/file"
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["read", "search", "list", "open", "create_folder", "create_file", "edit", "append", "rename_file", "move_file", "copy_file"],
                "description": "Action to perform on the filesystem (OpenClaw file standards)."
            },
            "path": {
                "type": "string",
                "description": "Path to the local file/directory (relative or absolute)."
            },
            "destination": {
                "type": "string",
                "description": "Destination path for move_file or copy_file."
            },
            "new_name": {
                "type": "string",
                "description": "New name for rename_file."
            },
            "old_text": {
                "type": "string",
                "description": "Target text to be replaced for edit action."
            },
            "new_text": {
                "type": "string",
                "description": "Replacement text for edit action."
            },
            "content": {
                "type": "string",
                "description": "Text content for create_file or append."
            },
            "query": {
                "type": "string",
                "description": "Filename glob pattern for searching (e.g. '*.txt')."
            },
            "locations": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Directories to search in (e.g. ['Desktop', 'Downloads']). Default is standard user directories."
            },
            "max_lines": {
                "type": "integer",
                "description": "Maximum number of lines to read (default: 200)."
            }
        },
        "required": ["action"]
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

    def _get_default_search_locations(self) -> List[str]:
        home = os.path.expanduser('~')
        return [
            os.path.join(home, "Desktop"),
            os.path.join(home, "Downloads"),
            os.path.join(home, "Documents"),
            os.path.join(home, "Pictures"),
            os.path.join(home, "Videos"),
            os.path.join(home, "Music")
        ]

    def _resolve_special_path(self, path: str) -> str:
        lower_path = path.lower()
        home = os.path.expanduser('~')
        specials = {
            "desktop": os.path.join(home, "Desktop"),
            "downloads": os.path.join(home, "Downloads"),
            "documents": os.path.join(home, "Documents"),
            "pictures": os.path.join(home, "Pictures"),
            "videos": os.path.join(home, "Videos"),
            "music": os.path.join(home, "Music")
        }
        for k, v in specials.items():
            if lower_path == k or lower_path == f"{k} folder":
                return v
        return path

    async def run(self, action: str = "read", path: str = "", query: str = "", locations: Optional[List[str]] = None, max_lines: int = 200, **kwargs: Any) -> Dict[str, Any]:
        if action == "read":
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
                "action": "read",
                "path": str(file_path),
                "total_lines": total_lines,
                "read_lines": len(selected_lines),
                "truncated": truncated,
                "content": "".join(selected_lines)
            }
            
        elif action == "search":
            if not query:
                raise ValueError("Query pattern must be provided for searching.")
                
            search_dirs = locations if locations else self._get_default_search_locations()
            results = []
            
            for loc in search_dirs:
                resolved_loc = Path(self._resolve_special_path(loc))
                if not resolved_loc.exists() or not resolved_loc.is_dir():
                    continue
                    
                for root, _, files in os.walk(str(resolved_loc)):
                    for name in fnmatch.filter(files, query):
                        if len(results) >= 20:
                            break
                        full_path = Path(root) / name
                        try:
                            stat = full_path.stat()
                            results.append({
                                "path": str(full_path),
                                "size_bytes": stat.st_size,
                                "modified_date": stat.st_mtime
                            })
                        except Exception:
                            continue
                    if len(results) >= 20:
                        break
                if len(results) >= 20:
                    break
                    
            return {
                "action": "search",
                "query": query,
                "results": results
            }
            
        elif action == "list":
            if not path.strip():
                path = "."
                
            resolved_path = Path(self._resolve_special_path(path))
            if not resolved_path.exists():
                raise FileNotFoundError(f"Path not found: {path}")
            if not resolved_path.is_dir():
                raise NotADirectoryError(f"Target is not a directory: {path}")
                
            if not self._is_safe_path(resolved_path):
                raise PermissionError(f"Access denied: Path '{path}' is outside allowed directory roots.")
                
            results = []
            try:
                for entry in os.scandir(resolved_path):
                    stat = entry.stat()
                    results.append({
                        "name": entry.name,
                        "is_dir": entry.is_dir(),
                        "size_bytes": stat.st_size,
                        "modified_time": stat.st_mtime
                    })
            except Exception as e:
                raise RuntimeError(f"Error listing directory: {e}")
                
            return {
                "action": "list",
                "path": str(resolved_path),
                "contents": results
            }
            
        elif action == "open":
            if not path.strip():
                raise ValueError("Path must be provided for opening.")
                
            resolved_path = self._resolve_special_path(path)
            if not os.path.exists(resolved_path):
                raise FileNotFoundError(f"Path not found: {resolved_path}")
                
            if os.name == 'nt':
                os.startfile(resolved_path)
            else:
                import subprocess
                if sys.platform == "darwin":
                    subprocess.Popen(['open', resolved_path])
                else:
                    subprocess.Popen(['xdg-open', resolved_path])
                    
            return {
                "action": "open",
                "path": resolved_path,
                "status": "opened"
            }
            
        elif action == "create_folder":
            if not path.strip():
                raise ValueError("Path must be provided for creating a folder.")
                
            raw_path = self._resolve_special_path(path)
            resolved_path = Path(raw_path)
            if not resolved_path.is_absolute() and len(resolved_path.parts) == 1:
                desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
                if os.path.exists(desktop):
                    resolved_path = Path(desktop) / raw_path
            
            try:
                os.makedirs(str(resolved_path), exist_ok=True)
                if not resolved_path.exists():
                    raise IOError(f"Could not verify folder creation at {resolved_path}")
                return {
                    "action": "create_folder",
                    "path": str(resolved_path.resolve()),
                    "status": "created"
                }
            except Exception as e:
                raise RuntimeError(f"Failed to create folder: {e}")

        elif action == "create_file":
            if not path.strip():
                raise ValueError("Path must be provided for creating a file.")
            raw_path = self._resolve_special_path(path)
            resolved_path = Path(raw_path)
            if not resolved_path.is_absolute() and len(resolved_path.parts) == 1:
                desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
                if os.path.exists(desktop):
                    resolved_path = Path(desktop) / raw_path

            resolved_path.parent.mkdir(parents=True, exist_ok=True)
            content = kwargs.get("content", "")
            resolved_path.write_text(content, encoding="utf-8")
            if not resolved_path.exists():
                raise IOError(f"Could not verify file creation at {resolved_path}")
            return {
                "action": "create_file",
                "path": str(resolved_path.resolve()),
                "status": "created"
            }

        elif action == "rename_file":
            new_name = kwargs.get("new_name") or kwargs.get("destination", "")
            if not path.strip() or not new_name.strip():
                raise ValueError("Both 'path' and 'new_name' are required for renaming.")
            old_path = Path(self._resolve_special_path(path))
            if not old_path.exists():
                raise FileNotFoundError(f"File not found: {path}")
            new_path = old_path.parent / new_name.strip()
            old_path.rename(new_path)
            return {
                "action": "rename_file",
                "old_path": str(old_path),
                "new_path": str(new_path),
                "status": "renamed"
            }

        elif action == "move_file":
            dest = kwargs.get("destination", "")
            if not path.strip() or not dest.strip():
                raise ValueError("Both 'path' and 'destination' are required for moving.")
            src_path = Path(self._resolve_special_path(path))
            dest_path = Path(self._resolve_special_path(dest))
            shutil.move(str(src_path), str(dest_path))
            return {
                "action": "move_file",
                "source": str(src_path),
                "destination": str(dest_path),
                "status": "moved"
            }

        elif action == "copy_file":
            dest = kwargs.get("destination", "")
            if not path.strip() or not dest.strip():
                raise ValueError("Both 'path' and 'destination' are required for copying.")
            src_path = Path(self._resolve_special_path(path))
            dest_path = Path(self._resolve_special_path(dest))
            if src_path.is_dir():
                shutil.copytree(str(src_path), str(dest_path), dirs_exist_ok=True)
            else:
                shutil.copy2(str(src_path), str(dest_path))
            return {
                "action": "copy_file",
                "source": str(src_path),
                "destination": str(dest_path),
                "status": "copied"
            }

        elif action == "edit":
            old_text = kwargs.get("old_text", "")
            new_text = kwargs.get("new_text", "")
            if not path.strip():
                raise ValueError("Path is required for edit action.")
            resolved_path = Path(self._resolve_special_path(path))
            if not resolved_path.exists():
                raise FileNotFoundError(f"File not found: {path}")
            if not self._is_safe_path(resolved_path):
                raise PermissionError(f"Access denied: Path '{path}' is outside allowed directory roots.")
            content = resolved_path.read_text(encoding="utf-8")
            if old_text not in content:
                raise ValueError(f"Target text '{old_text[:50]}' not found in '{path}'.")
            updated = content.replace(old_text, new_text, 1)
            resolved_path.write_text(updated, encoding="utf-8")
            return {
                "action": "edit",
                "path": str(resolved_path),
                "status": "edited",
                "replacements": 1
            }

        elif action == "append":
            content_to_add = kwargs.get("content", "")
            if not path.strip():
                raise ValueError("Path is required for append action.")
            resolved_path = Path(self._resolve_special_path(path))
            if not resolved_path.exists():
                raise FileNotFoundError(f"File not found: {path}")
            if not self._is_safe_path(resolved_path):
                raise PermissionError(f"Access denied: Path '{path}' is outside allowed directory roots.")
            with open(resolved_path, "a", encoding="utf-8") as f:
                f.write(content_to_add)
            return {
                "action": "append",
                "path": str(resolved_path),
                "status": "appended"
            }

        else:
            raise ValueError(f"Unknown action: {action}")

    def intent_patterns(self) -> list[dict]:
        def extract_read(m) -> dict:
            filepath = m.group(1).strip()
            if "." in filepath or "/" in filepath or "\\" in filepath:
                return {"action": "read", "path": filepath}
            return None

        def extract_search(m) -> dict:
            raw = m.group(1).strip() if m.lastindex else ""
            # Strip prefixes like "my computer for a file named", "files named", etc.
            clean = re.sub(r'^(?:(?:my\s+)?computer\s+(?:for\s+)?(?:a\s+)?(?:file|files)?\s*(?:named|called)?\s*|(?:my\s+)?pc\s+(?:for\s+)?(?:a\s+)?(?:file|files)?\s*(?:named|called)?\s*|for\s+files?\s+(?:named|called)\s*|(?:a\s+)?files?\s+(?:named|called)\s*)', '', raw, flags=re.I).strip()
            clean = clean.strip('\'"` ')

            # Check if user mentioned downloaded file
            if "downloaded" in clean.lower():
                type_match = re.search(r'\b(pdf|zip|docx?|xlsx?|csv|png|jpe?g|exe|txt)\b', clean, flags=re.I)
                q = f"*.{type_match.group(1)}" if type_match else "*"
                return {"action": "search", "query": q, "locations": ["~/Downloads"]}

            if not clean:
                clean = "*"
            return {"action": "search", "query": clean}
            
        def extract_list(m) -> dict:
            dirpath = m.group(1).strip()
            return {"action": "list", "path": dirpath}
            
        def extract_open(m) -> dict:
            path = m.group(1).strip()
            return {"action": "open", "path": path}

        def extract_create_folder(m) -> dict:
            raw = m.group(1).strip() if m.lastindex else ""
            clean_path = re.sub(r'^(?:(?:a\s+)?(?:new\s+)?(?:folder|directory)\s+(?:called|named)\s+|(?:called|named)\s+)', '', raw, flags=re.I).strip()
            clean_path = clean_path.strip('\'"` ')
            if not clean_path:
                clean_path = "new_folder"
            return {"action": "create_folder", "path": clean_path}

        def extract_create_file(m) -> dict:
            raw = m.group(1).strip() if m.lastindex else ""
            clean_path = re.sub(r'^(?:(?:a\s+)?(?:new\s+)?files?\s+(?:called|named)\s+|(?:called|named)\s+)', '', raw, flags=re.I).strip()
            
            content = ""
            content_match = re.search(r'\s+(?:with\s+content|with\s+text|containing|and\s+write)\s+[\'"]?(.+?)[\'"]?$', clean_path, flags=re.I)
            if content_match:
                content = content_match.group(1).strip()
                clean_path = clean_path[:content_match.start()].strip()
            
            clean_path = clean_path.strip('\'"` ')
            if not clean_path:
                clean_path = "new_file.txt"
            return {"action": "create_file", "path": clean_path, "content": content}

        def extract_rename(m) -> dict:
            return {"action": "rename_file", "path": m.group(1).strip(), "new_name": m.group(2).strip()}

        def extract_move(m) -> dict:
            return {"action": "move_file", "path": m.group(1).strip(), "destination": m.group(2).strip()}

        def extract_copy(m) -> dict:
            return {"action": "copy_file", "path": m.group(1).strip(), "destination": m.group(2).strip()}

        def extract_edit(m) -> dict:
            return {
                "action": "edit",
                "path": m.group(1).strip(),
                "old_text": m.group(2),
                "new_text": m.group(3)
            }

        def extract_append(m) -> dict:
            return {
                "action": "append",
                "path": m.group(1).strip(),
                "content": m.group(2)
            }

        return [
            {"pattern": r"^(?:read(?:\s+file)?|inspect(?:\s+file)?|view(?:\s+file)?|show(?:\s+file)?)\s+([a-zA-Z0-9_\-\.\/\\~]+)$", "extract": extract_read},
            {"pattern": r"^(?:search\s+(?:my\s+)?(?:computer|pc)\s+(?:for\s+)?(?:a\s+)?files?\s*(?:named|called)?|search\s+for\s+files?\s+(?:named|called)|find\s+(?:a\s+)?files?\s+(?:named|called)|find\s+file)\s+(.+)$", "extract": extract_search},
            {"pattern": r"^find\s+(?:the\s+)?(?:pdf|file|document|image)\s+(?:i\s+)?(?:downloaded|saved).*$", "extract": extract_search},
            {"pattern": r"^(?:create|make|touch)\s+(?:a\s+)?(?:new\s+)?(?:folder|directory)\b\s*(.*)$", "extract": extract_create_folder},
            {"pattern": r"^(?:create|make|touch)\s+(?:a\s+)?(?:new\s+)?files?\b\s*(.*)$", "extract": extract_create_file},
            {"pattern": r"^(?:create|make|touch)\s+([a-zA-Z0-9_\-]+\.[a-zA-Z0-9]+)$", "extract": extract_create_file},
            {"pattern": r"^(?:edit|modify)\s+(?:file\s+)?([^\s]+)\s+replace\s+[\"'](.+?)[\"']\s+with\s+[\"'](.+?)[\"']$", "extract": extract_edit},
            {"pattern": r"^(?:append\s+to|add\s+to)\s+(?:file\s+)?([^\s]+)\s+(.+)$", "extract": extract_append},
            {"pattern": r"^(?:rename(?:\s+file)?)\s+(.+)\s+to\s+(.+)$", "extract": extract_rename},
            {"pattern": r"^(?:move(?:\s+file)?)\s+(.+)\s+to\s+(.+)$", "extract": extract_move},
            {"pattern": r"^(?:copy(?:\s+file)?)\s+(.+)\s+to\s+(.+)$", "extract": extract_copy},
            {"pattern": r"^(?:open\s+file|open\s+folder)\s+(.+)$", "extract": extract_open},
            {"pattern": r"^open\s+([a-zA-Z0-9_\-\.\/\\~]+\.[a-zA-Z0-9]+)$", "extract": extract_open}
        ]

    def format_display(self, result) -> str:
        if not result.success:
            return f"I encountered an error executing {self.name}: {result.output}"
        out = result.output
        if isinstance(out, dict):
            action = out.get("action")
            if action == "read":
                path = out.get("path", "")
                lines_count = out.get("total_lines", 0)
                content = out.get("content", "")
                return f"Here is the content of `{path}` ({lines_count} lines):\n\n```\n{content[:1000]}\n```"
            elif action == "search":
                res = out.get("results", [])
                if not res:
                    return f"No files found matching '{out.get('query')}'."
                display = "\n".join([f"- {r['path']} ({r['size_bytes']} bytes)" for r in res])
                return f"Found {len(res)} files matching '{out.get('query')}':\n{display}"
            elif action == "list":
                res = out.get("contents", [])
                path = out.get("path")
                if not res:
                    return f"Directory `{path}` is empty."
                display = "\n".join([f"- {'[DIR] ' if r['is_dir'] else '[FILE]'} {r['name']} ({r['size_bytes']} bytes)" for r in res[:50]])
                return f"Contents of `{path}` ({len(res)} items):\n{display}"
            elif action == "open":
                return f"Opened {out.get('path')}."
            elif action == "create_folder":
                return f"Created folder `{out.get('path')}`."
            elif action == "create_file":
                return f"Created file `{out.get('path')}`."
            elif action == "edit":
                return f"Edited `{out.get('path')}`."
            elif action == "append":
                return f"Appended content to `{out.get('path')}`."
            elif action == "rename_file":
                return f"Renamed `{out.get('old_path')}` to `{out.get('new_path')}`."
            elif action == "move_file":
                return f"Moved `{out.get('source')}` to `{out.get('destination')}`."
            elif action == "copy_file":
                return f"Copied `{out.get('source')}` to `{out.get('destination')}`."
        return str(out)
