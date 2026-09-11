"""SQLite-based persistent memory system for Victor."""

import json
import os
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


class MemoryStore:
    """Manages short-term conversation, long-term facts/preferences, and task history."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            data_dir = Path("data")
            data_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = str(data_dir / "victor_memory.db")
        else:
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            self.db_path = db_path

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Create tables for preferences, facts, tasks, and conversations."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # User preferences (e.g., "preferred_video_duration": "< 20m")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS preferences (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at REAL NOT NULL
                )
            """)

            # Long-term facts (e.g., "User is studying compiler construction")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fact TEXT NOT NULL,
                    category TEXT NOT NULL DEFAULT 'general',
                    created_at REAL NOT NULL
                )
            """)

            # Task memory (history of multi-step autonomous tasks)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS task_memory (
                    id TEXT PRIMARY KEY,
                    goal TEXT NOT NULL,
                    steps_json TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    duration REAL NOT NULL,
                    created_at REAL NOT NULL
                )
            """)

            # Short-term chat history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp REAL NOT NULL
                )
            """)
            conn.commit()

    # --- Preferences ---

    def set_preference(self, key: str, value: str):
        with self._get_connection() as conn:
            conn.cursor().execute(
                "INSERT OR REPLACE INTO preferences (key, value, updated_at) VALUES (?, ?, ?)",
                (key, value, time.time()),
            )
            conn.commit()

    def get_preference(self, key: str, default: Optional[str] = None) -> Optional[str]:
        with self._get_connection() as conn:
            row = conn.cursor().execute("SELECT value FROM preferences WHERE key = ?", (key,)).fetchone()
            return row["value"] if row else default

    def list_preferences(self) -> Dict[str, str]:
        with self._get_connection() as conn:
            rows = conn.cursor().execute("SELECT key, value FROM preferences ORDER BY key ASC").fetchall()
            return {r["key"]: r["value"] for r in rows}

    def delete_preference(self, key: str):
        with self._get_connection() as conn:
            conn.cursor().execute("DELETE FROM preferences WHERE key = ?", (key,))
            conn.commit()

    # --- Long-Term Facts ---

    def add_fact(self, fact: str, category: str = "general") -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO facts (fact, category, created_at) VALUES (?, ?, ?)",
                (fact.strip(), category.lower(), time.time()),
            )
            conn.commit()
            return cursor.lastrowid

    def list_facts(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if category:
                rows = cursor.execute("SELECT * FROM facts WHERE category = ? ORDER BY created_at DESC", (category.lower(),)).fetchall()
            else:
                rows = cursor.execute("SELECT * FROM facts ORDER BY created_at DESC").fetchall()
            return [dict(r) for r in rows]

    def delete_fact(self, fact_id: int):
        with self._get_connection() as conn:
            conn.cursor().execute("DELETE FROM facts WHERE id = ?", (fact_id,))
            conn.commit()

    def search_facts(self, query: str) -> List[Dict[str, Any]]:
        """Search remembered facts matching keywords."""
        with self._get_connection() as conn:
            pattern = f"%{query.strip().lower()}%"
            rows = conn.cursor().execute(
                "SELECT * FROM facts WHERE LOWER(fact) LIKE ? OR LOWER(category) LIKE ? ORDER BY created_at DESC",
                (pattern, pattern),
            ).fetchall()
            return [dict(r) for r in rows]

    # --- Task Memory ---

    def save_task(self, task_id: str, goal: str, steps: List[Dict[str, Any]], outcome: str, duration: float):
        with self._get_connection() as conn:
            conn.cursor().execute(
                """
                INSERT OR REPLACE INTO task_memory (id, goal, steps_json, outcome, duration, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (task_id, goal, json.dumps(steps), outcome, duration, time.time()),
            )
            conn.commit()

    def list_tasks(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            rows = conn.cursor().execute(
                "SELECT * FROM task_memory ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            result = []
            for r in rows:
                item = dict(r)
                try:
                    item["steps"] = json.loads(item["steps_json"])
                except Exception:
                    item["steps"] = []
                del item["steps_json"]
                result.append(item)
            return result

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            row = conn.cursor().execute("SELECT * FROM task_memory WHERE id = ?", (task_id,)).fetchone()
            if not row:
                return None
            item = dict(row)
            try:
                item["steps"] = json.loads(item["steps_json"])
            except Exception:
                item["steps"] = []
            del item["steps_json"]
            return item

    # --- Summary for Agent Context ---

    def get_context_summary(self) -> str:
        """Compile a natural summary of user preferences and facts for LLM injection."""
        facts = self.list_facts()
        prefs = self.list_preferences()

        if not facts and not prefs:
            return ""

        lines = ["## Long-Term Memory & User Context:"]
        if prefs:
            lines.append("User Preferences:")
            for k, v in prefs.items():
                lines.append(f"- {k}: {v}")
        if facts:
            lines.append("Known Facts:")
            for f in facts[:8]:
                lines.append(f"- {f['fact']}")
        return "\n".join(lines)
