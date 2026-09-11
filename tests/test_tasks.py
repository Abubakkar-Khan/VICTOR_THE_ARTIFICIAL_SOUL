"""Unit tests for Victor Task Manager."""

import pytest
from victor.memory.store import MemoryStore
from victor.tasks.manager import TaskManager


def test_task_lifecycle(tmp_path):
    db_file = tmp_path / "test_tasks.db"
    mem = MemoryStore(str(db_file))
    tm = TaskManager(memory_store=mem)

    task = tm.create_task("Find compiler tutorials and open browser")
    assert task.status == "pending"

    tm.start_task(task.id)
    assert task.status == "running"

    step1 = task.add_step("Search Web", tool="web_search")
    step1.status = "completed"
    step1.output = "Retrieved 5 links"

    step2 = task.add_step("Search YouTube", tool="youtube")
    step2.status = "completed"
    step2.output = "Found 3 videos"

    tm.complete_task(task.id, outcome="Task successfully executed")
    assert task.status == "completed"
    assert task.duration >= 0

    all_tasks = tm.list_all_tasks()
    assert len(all_tasks) == 1
    assert all_tasks[0]["goal"] == "Find compiler tutorials and open browser"
    assert len(all_tasks[0]["steps"]) == 2
