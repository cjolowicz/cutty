"""Templates."""
from collections.abc import Iterable

from cutty.domain.files import RenderableFile
from cutty.domain.renderables import Renderable
from cutty.domain.variables import Value
from cutty.domain.varspecs import VariableSpecification


class Template:
    """A project template."""

    def __init__(
        self,
        *,
        variables: Iterable[VariableSpecification[Renderable[Value]]],
        files: Iterable[RenderableFile],
    ) -> None:
        """Initialize."""
        self.variables = tuple(variables)
        self.files = tuple(files)
