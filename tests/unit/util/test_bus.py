"""Tests for cutty.util.bus."""
import contextlib

import pytest

from cutty.util.bus import Bus
from cutty.util.bus import Context
from cutty.util.bus import Event


@pytest.fixture
def bus() -> Bus:
    """Return an event bus."""
    return Bus()


def test_events_publish(bus: Bus) -> None:
    """It invokes the handler."""
    events = []

    @bus.events.subscribe
    def handler(event: Event) -> None:
        events.append(event)

    event = Event()
    bus.events.publish(event)

    [seen] = events
    assert event is seen


def test_contexts_publish(bus: Bus) -> None:
    """It invokes the handler."""
    contexts = []

    @bus.contexts.subscribe
    def handler(context: Context) -> contextlib.AbstractContextManager[None]:
        contexts.append(context)
        return contextlib.nullcontext()

    context = Context()
    with bus.contexts.publish(context):
        pass

    [seen] = contexts
    assert context is seen


def test_events_subscribe_without_annotations(bus: Bus) -> None:
    """It fails when the handler has no type annotations."""
    with pytest.raises(Exception):

        @bus.events.subscribe
        def handler(event):  # type: ignore[no-untyped-def]
            pass


def test_contexts_subscribe_without_annotations(bus: Bus) -> None:
    """It fails when the handler has no type annotations."""
    with pytest.raises(Exception):

        @bus.contexts.subscribe
        def handler(event):  # type: ignore[no-untyped-def]
            pass
