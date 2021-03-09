"""Templates."""
from collections.abc import Iterable
from collections.abc import Iterator

from cutty.domain.files import File
from cutty.domain.files import RenderableFileRenderer
from cutty.domain.files import RenderableFileRepository
from cutty.domain.renderables import Renderable
from cutty.domain.variables import Value
from cutty.domain.varspecs import VariableBuilder
from cutty.domain.varspecs import VariableSpecification


class Template:
    """A project template."""

    def __init__(
        self,
        *,
        files: RenderableFileRepository,
        variables: Iterable[Renderable[VariableSpecification[Value]]],
    ) -> None:
        """Initialize."""
        self.files = files
        self.variables = tuple(variables)


class TemplateRenderer:
    """A renderer for templates."""

    def __init__(self, *, builder: VariableBuilder) -> None:
        """Initialize."""
        self.builder = builder

    def render(self, template: Template) -> Iterator[File]:
        """Render the template."""
        variables = self.builder.build(template.variables)
        renderer = RenderableFileRenderer(template.files)
        yield from renderer.render(variables)
