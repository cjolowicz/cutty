"""Unit tests for cutty.domain.hooks."""
import pytest

from cutty.domain.files import File
from cutty.domain.files import Mode
from cutty.domain.hooks import Hook
from cutty.domain.hooks import HookExecutor
from cutty.domain.hooks import HookManager
from cutty.domain.hooks import PostGenerateProject
from cutty.domain.hooks import PreGenerateProject
from cutty.filesystem.dict import DictFilesystem
from cutty.filesystem.path import Path
from cutty.filesystem.pure import PurePath
from cutty.util.bus import Bus
from cutty.util.bus import Event


class FakeHookExecutor(HookExecutor):
    """A hook executor that does nothing."""

    def execute(self, hook: Hook, project: Path) -> None:
        """Execute the hook."""


@pytest.mark.parametrize("eventtype", [PreGenerateProject, PostGenerateProject, Event])
def test_manager(bus: Bus, eventtype: type[Event]) -> None:
    """It subscribes the hooks."""
    file = File(PurePath(), Mode.DEFAULT, "")
    hook = Hook(file=file, event=eventtype)
    executor = FakeHookExecutor()
    manager = HookManager([hook], executor)
    manager.subscribe(bus)

    project = Path(filesystem=DictFilesystem({}))
    event = (
        eventtype(project)
        if issubclass(eventtype, PreGenerateProject)
        or issubclass(eventtype, PostGenerateProject)
        else eventtype()
    )
    bus.events.publish(event)
