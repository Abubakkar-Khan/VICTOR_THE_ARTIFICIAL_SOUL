"""Multi-step Autonomous Task Manager for Victor."""

import time
import uuid
from typing import Any, Dict, List, Optional
from dexter.memory.store import MemoryStore


class TaskStep:
    def __init__(self, step_id: str, name: str, tool: Optional[str] = None):
        self.step_id = step_id
        self.name = name
        self.tool = tool
        self.status = "pending"  # pending, running, completed, failed
        self.duration: float = 0.0
        self.output: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.step_id,
            "name": self.name,
            "tool": self.tool,
            "status": self.status,
            "duration": round(self.duration, 2),
            "output": self.output,
        }


class AutonomousTask:
    def __init__(self, goal: str, task_id: Optional[str] = None):
        self.id = task_id or f"task-{str(uuid.uuid4())[:8]}"
        self.goal = goal
        self.status = "pending"  # pending, running, completed, failed
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.steps: List[TaskStep] = []
        self.outcome: Optional[str] = None

    @property
    def duration(self) -> float:
        if self.end_time:
            return round(self.end_time - self.start_time, 2)
        return round(time.time() - self.start_time, 2)

    def add_step(self, name: str, tool: Optional[str] = None) -> TaskStep:
        step = TaskStep(step_id=f"step-{len(self.steps) + 1}", name=name, tool=tool)
        self.steps.append(step)
        return step

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "goal": self.goal,
            "status": self.status,
            "duration": self.duration,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "steps": [s.to_dict() for s in self.steps],
            "outcome": self.outcome,
        }


class TaskManager:
    """Manages active tasks, multi-step subtask tracking, and persistence."""

    def __init__(self, memory_store: Optional[MemoryStore] = None):
        self.memory_store = memory_store or MemoryStore()
        self.active_tasks: Dict[str, AutonomousTask] = {}

    def create_task(self, goal: str) -> AutonomousTask:
        task = AutonomousTask(goal=goal)
        self.active_tasks[task.id] = task
        return task

    def get_task(self, task_id: str) -> Optional[AutonomousTask]:
        return self.active_tasks.get(task_id)

    def start_task(self, task_id: str):
        task = self.get_task(task_id)
        if task:
            task.status = "running"

    def complete_task(self, task_id: str, outcome: str):
        task = self.get_task(task_id)
        if task:
            task.status = "completed"
            task.end_time = time.time()
            task.outcome = outcome
            # Persist to SQLite task memory
            self.memory_store.save_task(
                task_id=task.id,
                goal=task.goal,
                steps=[s.to_dict() for s in task.steps],
                outcome=task.outcome,
                duration=task.duration,
            )

    def fail_task(self, task_id: str, error: str):
        task = self.get_task(task_id)
        if task:
            task.status = "failed"
            task.end_time = time.time()
            task.outcome = f"Failed: {error}"
            self.memory_store.save_task(
                task_id=task.id,
                goal=task.goal,
                steps=[s.to_dict() for s in task.steps],
                outcome=task.outcome,
                duration=task.duration,
            )

    def list_active_tasks(self) -> List[Dict[str, Any]]:
        return [t.to_dict() for t in self.active_tasks.values()]

    def list_all_tasks(self) -> List[Dict[str, Any]]:
        """Combine live tasks with historical tasks from memory."""
        live = [t.to_dict() for t in self.active_tasks.values()]
        persisted = self.memory_store.list_tasks(limit=30)
        # Avoid duplicates
        live_ids = {t["id"] for t in live}
        combined = live + [p for p in persisted if p["id"] not in live_ids]
        return combined
