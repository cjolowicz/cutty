"""Binding variables."""
from collections.abc import Sequence

from cutty.templates.domain.render import Renderer
from cutty.variables.binders import Binder
from cutty.variables.binders import override
from cutty.variables.bindings import Binding
from cutty.variables.variables import Variable


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


def bindvariables(
    variables: Sequence[Variable],
    render: Renderer,
    binder: Binder,
    *,
    bindings: Sequence[Binding],
) -> Sequence[Binding]:
    """Bind the template variables."""
    binder = override(binder, bindings)
    return renderbind(render, binder, variables)
