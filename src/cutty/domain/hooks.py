"""Hooks."""
from collections.abc import Callable
from collections.abc import Iterable
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


class HookManager:
    """Hook manager."""

    def __init__(self, hooks: Iterable[Hook], executehook: HookExecutor) -> None:
        """Initialize."""
        self.hooks = tuple(hooks)
        self.executehook = executehook

    def subscribe(self, bus: Bus) -> None:
        """Subscribe the hooks."""
        for hook in self.hooks:
            if hook.event is PreGenerateProject:

                @bus.events.subscribe
                def _(event: PreGenerateProject) -> None:
                    self.executehook(hook, event.project)

            elif hook.event is PostGenerateProject:

                @bus.events.subscribe
                def _(event: PostGenerateProject) -> None:
                    self.executehook(hook, event.project)
