"""Hooks."""
from collections.abc import Callable
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Union

from cutty.domain.bindings import Binding
from cutty.domain.files import File
from cutty.domain.render import Renderer
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

    path: Path
    event: type[Event]


HookExecutor = Callable[[File, Path], None]


def registerhook(
    hook: Hook,
    render: Renderer,
    bindings: Sequence[Binding],
    executehook: HookExecutor,
    bus: Bus,
) -> None:
    """Subscribe the hook to its event."""

    def runhook(event: Union[PreGenerateProject, PostGenerateProject]) -> None:
        """Render and execute the hook."""
        hookfile = File.load(hook.path)
        hookfile = render(hookfile, bindings)
        executehook(hookfile, event.project)

    if hook.event is PreGenerateProject:

        @bus.events.subscribe
        def _(event: PreGenerateProject) -> None:
            runhook(event)

    elif hook.event is PostGenerateProject:

        @bus.events.subscribe
        def _(event: PostGenerateProject) -> None:
            runhook(event)
