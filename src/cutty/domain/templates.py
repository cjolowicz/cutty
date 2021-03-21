"""Templates."""
from collections.abc import Iterable
from collections.abc import Iterator
from collections.abc import Sequence
from dataclasses import dataclass

from cutty.domain.binders import Binder
from cutty.domain.bindings import Binding
from cutty.domain.files import File
from cutty.domain.files import FileStorage
from cutty.domain.render import Renderer
from cutty.domain.variables import Variable


@dataclass
class TemplateConfig:
    """Template configuration."""

    settings: tuple[Binding, ...]
    variables: tuple[Variable, ...]


class InvalidPathComponent(Exception):
    """The rendered path has an invalid component."""


class Template:
    """A project template."""

    def __init__(
        self,
        *,
        config: TemplateConfig,
        renderer: Renderer,
        files: Iterable[File],
        hooks: Iterable[File] = (),
    ) -> None:
        """Initialize."""
        self.config = config
        self.files = files
        self.hooks = hooks
        self.renderer = renderer

    def render(self, bindings: Sequence[Binding]) -> Iterator[File]:
        """Render the template."""
        for file in self.files:
            file = self.renderer(file, bindings)

            if not all(file.path.parts):
                # FIXME: Shouldn't have rendered the blob at all.
                # FIXME: Can we avoid traversing that directory?
                continue

            if any(
                "/" in part or "\\" in part or part == "." or part == ".."
                for part in file.path.parts
            ):
                raise InvalidPathComponent(str(file.path))

            yield file


class TemplateRenderer:
    """A renderer for templates."""

    def __init__(self, *, binder: Binder, storage: FileStorage) -> None:
        """Initialize."""
        self.binder = binder
        self.storage = storage

    def render(self, template: Template) -> None:
        """Render the template."""
        bindings = self.binder.bind(
            template.config.variables,
            template.config.settings,
            template.renderer,
        )

        for file in template.render(bindings):
            self.storage.store(file)
