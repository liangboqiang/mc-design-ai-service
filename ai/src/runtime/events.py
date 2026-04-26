from __future__ import annotations

from collections import defaultdict
from typing import Callable

from .types import Event

Subscriber = Callable[[Event], None]


class EventBus:
    def __init__(self):
        self._events: list[Event] = []
        self._subscribers: dict[str, list[Subscriber]] = defaultdict(list)

    def subscribe(self, event_name: str, callback: Subscriber) -> None:
        self._subscribers[event_name].append(callback)

    def emit(self, event_name: str, **payload) -> Event:
        event = Event(name=event_name, payload=payload)
        self._events.append(event)
        for callback in [*self._subscribers.get(event_name, []), *self._subscribers.get("*", [])]:
            try:
                callback(event)
            except Exception:
                pass
        return event

    def recent(self, limit: int = 20) -> list[Event]:
        return self._events[-limit:]
