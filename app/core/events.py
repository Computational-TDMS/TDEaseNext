"""
Event Bus - 事件总线

发布/订阅模式，统一处理日志流、状态变更、WebSocket 推送、AI 监控。
"""
import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    NODE_STARTED = "node_started"
    NODE_COMPLETED = "node_completed"
    NODE_FAILED = "node_failed"
    NODE_SKIPPED = "node_skipped"
    LOG = "log"
    EXECUTION_STARTED = "execution_started"
    EXECUTION_COMPLETED = "execution_completed"
    EXECUTION_FAILED = "execution_failed"


@dataclass
class WorkflowEvent:
    type: EventType
    execution_id: Optional[str] = None
    node_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)


class EventBus:
    """轻量级事件总线"""

    def __init__(self):
        self._handlers: Dict[EventType, List[Callable]] = {
            et: [] for et in EventType
        }
        self._handlers_any: List[Callable] = []

    def subscribe(self, event_type: EventType, handler: Callable[[WorkflowEvent], None]) -> None:
        self._handlers[event_type].append(handler)

    def subscribe_all(self, handler: Callable[[WorkflowEvent], None]) -> None:
        self._handlers_any.append(handler)

    def unsubscribe(self, event_type: EventType, handler: Callable) -> None:
        if handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)

    def publish(self, event: WorkflowEvent) -> None:
        for h in self._handlers.get(event.type, []):
            try:
                h(event)
            except Exception as e:
                logger.exception("Event handler error: %s", e)
        for h in self._handlers_any:
            try:
                h(event)
            except Exception as e:
                logger.exception("Event handler error: %s", e)

    async def publish_async(self, event: WorkflowEvent) -> None:
        for h in self._handlers.get(event.type, []):
            try:
                if asyncio.iscoroutinefunction(h):
                    await h(event)
                else:
                    h(event)
            except Exception as e:
                logger.exception("Event handler error: %s", e)
        for h in self._handlers_any:
            try:
                if asyncio.iscoroutinefunction(h):
                    await h(event)
                else:
                    h(event)
            except Exception as e:
                logger.exception("Event handler error: %s", e)


# 全局单例
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus
