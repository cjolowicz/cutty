"""Templates."""
import contextlib
from collections.abc import Iterable
from collections.abc import Iterator

from cutty.domain.files import File
from cutty.domain.files import RenderableFileLoader
from cutty.domain.paths import EmptyPathComponent
from cutty.domain.renderables import Renderable
from cutty.domain.variables import Value
from cutty.domain.varspecs import VariableBuilder
from cutty.domain.varspecs import VariableSpecification


class Template:
    """A project template."""

    def __init__(
        self,
        *,
        loader: RenderableFileLoader,
        variables: Iterable[VariableSpecification[Renderable[Value]]],
    ) -> None:
        """Initialize."""
        self.loader = loader
        self.variables = tuple(variables)

    def render(self, builder: VariableBuilder) -> Iterator[File]:
        """Render the template."""
        variables = builder.build(self.variables)

        for file in self.loader.load():
            with contextlib.suppress(EmptyPathComponent):
                yield file.render(variables)
