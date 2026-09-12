---
name: file-management
description: Inspect, search, create, edit, append, and organize files in workspace and desktop directories.
---

# File Management Skill

## Capabilities
- Read file content (`filesystem.read`).
- Create files on Desktop or workspace (`filesystem.create_file`).
- Edit existing files by targeted string replacement (`filesystem.edit`).
- Append content to files (`filesystem.append`).
- Search files across Desktop, Downloads, and Documents (`filesystem.search`).
- List directory entries (`filesystem.list`).
- Open files and folders with native OS viewers (`filesystem.open`).

## Workflow Guidelines
1. When creating files without a specific directory path, place them on the Desktop so the user can easily see them.
2. Verify file existence immediately after file creation or editing.
3. For incremental edits, use `filesystem.edit` with exact target text replacement.
