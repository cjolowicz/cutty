"""Binding variables."""
from collections.abc import Sequence

from cutty.rendering.domain.render import Renderer
from cutty.variables.domain.binders import Binder
from cutty.variables.domain.bindings import Binding
from cutty.variables.domain.variables import Variable


def renderbind(
    render: Renderer, binder: Binder, variables: Sequence[Variable]
) -> Sequence[Binding]:
    """Successively render and bind variables."""
    bindings: list[Binding] = []
    for variable in variables:
        variable = render(variable, bindings)
        binding = binder(variable)
        bindings.append(binding)
    return bindings
