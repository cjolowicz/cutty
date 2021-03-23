"""Hooks."""
import abc
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


class HookExecutor(abc.ABC):
    """Something that can execute a hook."""

    @abc.abstractmethod
    def execute(self, hook: Hook, project: Path) -> None:
        """Execute the hook."""


class HookManager:
    """Hook manager."""

    def __init__(self, hooks: Iterable[Hook], executor: HookExecutor) -> None:
        """Initialize."""
        self.hooks = tuple(hooks)
        self.executor = executor

    def subscribe(self, bus: Bus) -> None:
        """Subscribe the hooks."""
        for hook in self.hooks:
            if hook.event is PreGenerateProject:

                @bus.events.subscribe
                def _(event: PreGenerateProject) -> None:
                    self.executor.execute(hook, event.project)

            elif hook.event is PostGenerateProject:

                @bus.events.subscribe
                def _(event: PostGenerateProject) -> None:
                    self.executor.execute(hook, event.project)
