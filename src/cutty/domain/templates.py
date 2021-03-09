"""Templates."""
from collections.abc import Iterable

from cutty.domain.files import File
from cutty.domain.renderables import Renderable
from cutty.domain.variables import Value
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
