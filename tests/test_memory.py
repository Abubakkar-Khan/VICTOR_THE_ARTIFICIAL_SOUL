"""Unit tests for Victor SQLite Memory Store."""

import pytest
from dexter.memory.store import MemoryStore


def test_memory_preferences(tmp_path):
    db_file = tmp_path / "test_memory.db"
    store = MemoryStore(str(db_file))

    store.set_preference("preferred_video_length", "< 20m")
    store.set_preference("theme", "minimal_dark")

    assert store.get_preference("preferred_video_length") == "< 20m"
    assert store.get_preference("theme") == "minimal_dark"
    assert store.get_preference("nonexistent", "default_val") == "default_val"

    prefs = store.list_preferences()
    assert len(prefs) == 2

    store.delete_preference("theme")
    assert store.get_preference("theme") is None


def test_memory_facts(tmp_path):
    db_file = tmp_path / "test_memory.db"
    store = MemoryStore(str(db_file))

    fact_id = store.add_fact("User is researching compiler optimization in Rust", category="study")
    assert fact_id > 0

    facts = store.list_facts()
    assert len(facts) == 1
    assert "compiler optimization" in facts[0]["fact"]

    search_hits = store.search_facts("rust")
    assert len(search_hits) == 1

    summary = store.get_context_summary()
    assert "compiler optimization in Rust" in summary

    store.delete_fact(fact_id)
    assert len(store.list_facts()) == 0


def test_task_memory(tmp_path):
    db_file = tmp_path / "test_memory.db"
    store = MemoryStore(str(db_file))

    steps = [
        {"id": "step-1", "name": "Search YouTube", "status": "completed"},
        {"id": "step-2", "name": "Summarize result", "status": "completed"},
    ]
    store.save_task("task-101", "Find beginner compiler course", steps, "Found 3 good tutorials", 4.5)

    tasks = store.list_tasks()
    assert len(tasks) == 1
    assert tasks[0]["goal"] == "Find beginner compiler course"
    assert len(tasks[0]["steps"]) == 2
