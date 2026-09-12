"""OpenClaw-style Skills Subsystem for Victor/Dexter.

Discovers, parses, and manages SKILL.md instruction packs across workspace
and built-in skills directories.
"""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml


@dataclass
class Skill:
    """Represents an OpenClaw SKILL.md instruction pack."""
    name: str
    description: str
    instructions: str
    path: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def summary(self) -> str:
        return f"- **{self.name}**: {self.description}"


class SkillManager:
    """Discovers and manages modular skills (OpenClaw standard)."""

    def __init__(self, workspace_dir: Optional[str] = None):
        self.workspace_dir = Path(workspace_dir) if workspace_dir else Path.cwd()
        self._skills: Dict[str, Skill] = {}
        self.reload_skills()

    def reload_skills(self):
        """Scans workspace and built-in directories for SKILL.md packs."""
        self._skills.clear()

        # 1. Built-in skills
        builtin_root = Path(__file__).parent / "builtin"
        if builtin_root.exists():
            self._scan_directory(builtin_root)

        # 2. Workspace skills (take precedence)
        workspace_skills = self.workspace_dir / "skills"
        if workspace_skills.exists():
            self._scan_directory(workspace_skills)

    def _scan_directory(self, root: Path):
        for entry in root.iterdir():
            if entry.is_dir():
                skill_file = entry / "SKILL.md"
                if skill_file.exists() and skill_file.is_file():
                    skill = self._parse_skill_file(skill_file, default_name=entry.name)
                    if skill:
                        self._skills[skill.name.lower()] = skill

    def _parse_skill_file(self, file_path: Path, default_name: str) -> Optional[Skill]:
        try:
            raw = file_path.read_text(encoding="utf-8")
        except Exception:
            return None

        # Check for YAML frontmatter
        metadata = {}
        instructions = raw.strip()

        fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", raw, re.DOTALL)
        if fm_match:
            frontmatter_text = fm_match.group(1)
            instructions = fm_match.group(2).strip()
            try:
                parsed = yaml.safe_load(frontmatter_text)
                if isinstance(parsed, dict):
                    metadata = parsed
            except Exception:
                pass

        name = metadata.get("name") or default_name
        description = metadata.get("description") or f"Skill instructions for {name}."

        return Skill(
            name=str(name).strip(),
            description=str(description).strip(),
            instructions=instructions,
            path=str(file_path.resolve()),
            metadata=metadata
        )

    def list_skills(self) -> List[Skill]:
        return list(self._skills.values())

    def get_skill(self, name: str) -> Optional[Skill]:
        return self._skills.get(name.lower().strip())

    def get_prompt_injection(self) -> str:
        """Inject brief skills index into system prompt."""
        skills = self.list_skills()
        if not skills:
            return ""

        lines = ["## Active Skills (OpenClaw Architecture)"]
        for s in skills:
            lines.append(s.summary())
        lines.append("\nTo view or follow a skill, apply its specified steps and tool sequences.")
        return "\n".join(lines)
