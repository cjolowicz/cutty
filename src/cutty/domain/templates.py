"""Templates."""
from collections.abc import Iterable
from dataclasses import dataclass

from cutty.domain.files import File
from cutty.domain.files import FileStorage
from cutty.domain.files import renderfiles
from cutty.domain.renderables import Renderable
from cutty.domain.variables import Value
from cutty.domain.varspecs import VariableBuilder
from cutty.domain.varspecs import VariableSpecification


@dataclass
class TemplateConfig:
    """Template configuration."""

    variables: tuple[VariableSpecification[Value], ...]


class Template:
    """A project template."""

    def __init__(
        self,
        *,
        variables: Iterable[Renderable[VariableSpecification[Value]]],
        files: Iterable[Renderable[File]],
        hooks: Iterable[Renderable[File]] = (),
    ) -> None:
        """Initialize."""
        self.variables = tuple(variables)
        self.files = files
        self.hooks = hooks


class TemplateRenderer:
    """A renderer for templates."""

    def __init__(self, *, builder: VariableBuilder, storage: FileStorage) -> None:
        """Initialize."""
        self.builder = builder
        self.storage = storage

    def render(self, template: Template) -> None:
        """Render the template."""
        variables = self.builder.build(template.variables)
        for file in renderfiles(template.files, variables):
            self.storage.store(file)
