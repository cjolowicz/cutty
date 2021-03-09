"""Templates."""
from collections.abc import Iterable
from collections.abc import Iterator

from cutty.domain.files import File
from cutty.domain.files import renderfiles
from cutty.domain.renderables import Renderable
from cutty.domain.variables import Value
from cutty.domain.varspecs import VariableBuilder
from cutty.domain.varspecs import VariableSpecification


class Template:
    """A project template."""

    def __init__(
        self,
        *,
        files: Iterable[Renderable[File]],
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
        yield from renderfiles(template.files, variables)
