"""Unit tests for cutty.domain.hooks."""
import pytest

from cutty.domain.files import File
from cutty.domain.hooks import Hook
from cutty.domain.hooks import PostGenerateProject
from cutty.domain.hooks import PreGenerateProject
from cutty.domain.hooks import registerhook
from cutty.domain.render import Renderer
from cutty.filesystem.dict import DictFilesystem
from cutty.filesystem.path import Path
from cutty.util.bus import Bus
from cutty.util.bus import Event


def executehook(hookfile: File, project: Path) -> None:
    """A hook executor that does nothing."""


@pytest.mark.parametrize("eventtype", [PreGenerateProject, PostGenerateProject, Event])
def test_registerhook(render: Renderer, bus: Bus, eventtype: type[Event]) -> None:
    """It subscribes the hooks."""
    hookpath = Path("hook", filesystem=DictFilesystem({"hook": ""}))
    hook = Hook(path=hookpath, event=eventtype)

    registerhook(hook, render, [], executehook, bus)

    project = Path(filesystem=DictFilesystem({}))
    event = (
        eventtype(project)
        if issubclass(eventtype, PreGenerateProject)
        or issubclass(eventtype, PostGenerateProject)
        else eventtype()
    )
    bus.events.publish(event)
