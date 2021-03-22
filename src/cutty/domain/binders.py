"""Binding variables."""
from collections.abc import Callable
from collections.abc import Sequence
from typing import Protocol

from cutty.domain.bindings import Binding
from cutty.domain.render import Renderer
from cutty.domain.variables import Variable


Binder = Callable[[Variable], Binding]


def binddefault(variable: Variable) -> Binding:
    """Bind a variable to its default value."""
    return Binding(variable.name, variable.default)


class RenderBinder(Protocol):
    """Protocol for rendering and binding variables."""

    def __call__(
        self, variables: Sequence[Variable], *, render: Renderer
    ) -> Sequence[Binding]:
        """Bind the variables."""


def create_render_binder(bind: Binder) -> RenderBinder:
    """Create a rendering binder."""

    def _renderbind(
        variables: Sequence[Variable], *, render: Renderer
    ) -> Sequence[Binding]:
        bindings: list[Binding] = []
        for variable in variables:
            variable = render(variable, bindings)
            binding = bind(variable)
            bindings.append(binding)
        return bindings

    return _renderbind


default_binder = create_render_binder(binddefault)
