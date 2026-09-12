"""Event-driven communication bus for Victor."""

import asyncio
import time
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentEvent(BaseModel):
    """Base event model emitted across the Victor system."""
    topic: str
    timestamp: float = Field(default_factory=time.time)
    data: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic": self.topic,
            "timestamp": self.timestamp,
            "data": self.data,
        }


class EventBus:
    """Async pub/sub event bus enabling decoupled UI, CLI, and tool observability."""

    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[AgentEvent], Any]]] = {}
        self._all_subscribers: List[Callable[[AgentEvent], Any]] = []

    def subscribe(self, callback: Callable[[AgentEvent], Any], topic: Optional[str] = None):
        """Subscribe a callback to a specific topic or all topics if topic is None."""
        if topic is None or topic == "*":
            if callback not in self._all_subscribers:
                self._all_subscribers.append(callback)
        else:
            if topic not in self._subscribers:
                self._subscribers[topic] = []
            if callback not in self._subscribers[topic]:
                self._subscribers[topic].append(callback)

    def unsubscribe(self, callback: Callable[[AgentEvent], Any], topic: Optional[str] = None):
        """Unsubscribe a callback."""
        if topic is None or topic == "*":
            if callback in self._all_subscribers:
                self._all_subscribers.remove(callback)
        elif topic in self._subscribers and callback in self._subscribers[topic]:
            self._subscribers[topic].remove(callback)

    async def emit(self, topic: str, **data: Any):
        """Emit an event asynchronously to all matching subscribers."""
        event = AgentEvent(topic=topic, data=data)
        callbacks = list(self._all_subscribers) + list(self._subscribers.get(topic, []))
        
        for cb in callbacks:
            try:
                if asyncio.iscoroutinefunction(cb):
                    await cb(event)
                else:
                    cb(event)
            except Exception as err:
                # Log or suppress subscriber error without crashing the bus
                print(f"[EventBus] Error in subscriber for topic '{topic}': {err}")

    def emit_sync(self, topic: str, **data: Any):
        """Helper to emit events from synchronous code when an event loop is running."""
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.emit(topic, **data))
        except RuntimeError:
            asyncio.run(self.emit(topic, **data))


# Global default event bus instance
global_event_bus = EventBus()
