"""Event bus.

This module defines a :class:`Bus` class for publishing events and subscribing
handlers to them.

Events must derive from :class:`Event`. Handlers are functions that take the
event as an argument. The function must have type annotations, to allow the bus
to determine which handlers to invoke when an event is published.

>>> class Timber(Event):
...     pass
...
>>> def shout(event: Timber):
...     print("Timber!")
...
>>> bus = Bus()
>>> bus.events.subscribe(shout)
>>> bus.events.publish(Timber())
Timber!

Contexts are a special kind of event that has a start and an end. Handlers for
contexts must return a context manager, which is invoked on entering and exiting
the context.

>>> class Copy(Context):
...     pass
...
>>> import contextlib
...
>>> @contextlib.contextmanager
... def handle_copy(context: Copy):
...     print("starting copy...")
...     try:
...         yield
...     except Exception:
...         print("copy failed!")
...         raise
...     else:
...         print("copy complete.")
...
>>> bus.contexts.subscribe(handle_copy)
>>> with bus.contexts.publish(Copy()):
...     print("copy: file a")
...     print("copy: file b")
starting copy...
copy: file a
copy: file b
copy complete.
"""
from collections import defaultdict
from collections.abc import Iterator
from contextlib import AbstractContextManager
from contextlib import contextmanager
from contextlib import ExitStack
from typing import Any
from typing import get_type_hints
from typing import Protocol
from typing import TypeVar


__all__ = [
    "Bus",
    "Context",
    "Event",
]


class Event:
    """An event can be published on the bus, and subscribed to."""


class Context:
    """A context is an event with a duration."""


_EventT_contra = TypeVar("_EventT_contra", bound=Event, contravariant=True)
_ContextT_contra = TypeVar("_ContextT_contra", bound=Context, contravariant=True)


class _EventHandler(Protocol[_EventT_contra]):
    """Handler for an event."""

    def __call__(self, event: _EventT_contra) -> None:
        """Invoke the handler."""


class _ContextHandler(Protocol[_ContextT_contra]):
    """Handler for a context."""

    def __call__(self, context: _ContextT_contra) -> AbstractContextManager[None]:
        """Invoke the handler."""


class _Events:
    """Publish and subscribe to events."""

    def __init__(self) -> None:
        """Initialize."""
        self.handlers: dict[
            type[Event],
            list[_EventHandler[Any]],
        ] = defaultdict(list)

    def publish(self, event: Event) -> None:
        """Publish an event on the bus."""
        handlers = self.handlers[type(event)]
        for handler in handlers:
            handler(event)

    def subscribe(
        self, handler: _EventHandler[_EventT_contra]
    ) -> _EventHandler[_EventT_contra]:
        """Subscribe to an event."""
        event_type = next(hint for hint in get_type_hints(handler).values())
        self.handlers[event_type].append(handler)
        return handler


class _Contexts:
    """Publish and subscribe to contexts."""

    def __init__(self) -> None:
        """Initialize."""
        self.handlers: dict[
            type[Context],
            list[_ContextHandler[Any]],
        ] = defaultdict(list)

    @contextmanager
    def publish(self, event: Context) -> Iterator[None]:
        """Publish a context."""
        handlers = self.handlers[type(event)]
        with ExitStack() as stack:
            for handler in handlers:
                stack.enter_context(handler(event))
            yield

    def subscribe(
        self, handler: _ContextHandler[_ContextT_contra]
    ) -> _ContextHandler[_ContextT_contra]:
        """Subscribe to a context."""
        event_type = next(hint for hint in get_type_hints(handler).values())
        self.handlers[event_type].append(handler)
        return handler


class Bus:
    """Event bus."""

    def __init__(self) -> None:
        """Initialize."""
        self.events = _Events()
        self.contexts = _Contexts()
