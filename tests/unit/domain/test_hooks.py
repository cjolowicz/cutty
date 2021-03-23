"""Unit tests for cutty.domain.hooks."""
import pytest

from cutty.domain.files import File
from cutty.domain.files import Mode
from cutty.domain.hooks import Hook
from cutty.domain.hooks import PostGenerateProject
from cutty.domain.hooks import PreGenerateProject
from cutty.domain.hooks import registerhook
from cutty.filesystem.dict import DictFilesystem
from cutty.filesystem.path import Path
from cutty.filesystem.pure import PurePath
from cutty.util.bus import Bus
from cutty.util.bus import Event


def executehook(hook: Hook, project: Path) -> None:
    """A hook executor that does nothing."""


@pytest.mark.parametrize("eventtype", [PreGenerateProject, PostGenerateProject, Event])
def test_manager(bus: Bus, eventtype: type[Event]) -> None:
    """It subscribes the hooks."""
    file = File(PurePath(), Mode.DEFAULT, "")
    hook = Hook(file=file, event=eventtype)

    registerhook(hook, executehook, bus)

    project = Path(filesystem=DictFilesystem({}))
    event = (
        eventtype(project)
        if issubclass(eventtype, PreGenerateProject)
        or issubclass(eventtype, PostGenerateProject)
        else eventtype()
    )
    bus.events.publish(event)
