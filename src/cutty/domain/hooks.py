"""Hooks."""
from collections.abc import Callable
from dataclasses import dataclass

from cutty.domain.files import File
from cutty.filesystem.path import Path
from cutty.util.bus import Bus
from cutty.util.bus import Event


@dataclass
class PreGenerateProject(Event):
    """This event is published before the project is generated."""

    project: Path


@dataclass
class PostGenerateProject(Event):
    """This event is published after the project is generated."""

    project: Path


@dataclass
class Hook:
    """Hook."""

    file: File
    event: type[Event]


HookExecutor = Callable[[Hook, Path], None]


def registerhook(hook: Hook, executehook: HookExecutor, bus: Bus) -> None:
    """Subscribe the hook to its event."""
    if hook.event is PreGenerateProject:

        @bus.events.subscribe
        def _(event: PreGenerateProject) -> None:
            executehook(hook, event.project)

    elif hook.event is PostGenerateProject:

        @bus.events.subscribe
        def _(event: PostGenerateProject) -> None:
            executehook(hook, event.project)
