"""Unit tests for cutty.domain.hooks."""
import pytest

from cutty.domain.files import Buffer
from cutty.domain.files import Mode
from cutty.domain.files import Path
from cutty.domain.hooks import Hook
from cutty.domain.hooks import HookExecutor
from cutty.domain.hooks import HookManager
from cutty.domain.hooks import PostGenerateProject
from cutty.domain.hooks import PreGenerateProject
from cutty.util.bus import Bus
from cutty.util.bus import Event


class FakeHookExecutor(HookExecutor):
    """A hook executor that does nothing."""

    def execute(self, hook: Hook) -> None:
        """Execute the hook."""


@pytest.mark.parametrize("event", [PreGenerateProject, PostGenerateProject, Event])
def test_manager(bus: Bus, event: type[Event]) -> None:
    """It subscribes the hooks."""
    file = Buffer(Path(()), Mode.DEFAULT, "")
    hook = Hook(file=file, event=event)
    executor = FakeHookExecutor()
    manager = HookManager([hook], executor)
    manager.subscribe(bus)
    bus.events.publish(event())
