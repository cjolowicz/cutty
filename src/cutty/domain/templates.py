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
        variables: Iterable[Renderable[VariableSpecification[Value]]],
        files: Iterable[Renderable[File]],
        hooks: Iterable[Renderable[File]] = (),
    ) -> None:
        """Initialize."""
        self.variables = tuple(variables)
        self.files = files
        self.hooks = hooks
