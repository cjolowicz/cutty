"""Binding variables."""
from collections.abc import Callable
from collections.abc import Sequence

from cutty.templates.domain.render import Renderer
from cutty.variables.binders import binddefault
from cutty.variables.binders import Binder
from cutty.variables.binders import override
from cutty.variables.bindings import Binding
from cutty.variables.variables import Variable


RenderingBinder = Callable[[Renderer, Sequence[Variable]], Sequence[Binding]]


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


def renderbindwith(binder: Binder) -> RenderingBinder:
    """Render and bind variables using the given binder."""
    return lambda render, variables: renderbind(render, binder, variables)


def bindvariables(
    variables: Sequence[Variable],
    render: Renderer,
    prompt: Binder,
    *,
    interactive: bool,
    bindings: Sequence[Binding],
) -> Sequence[Binding]:
    """Bind the template variables."""
    binder: Binder = prompt if interactive else binddefault
    binder = override(binder, bindings)
    return renderbindwith(binder)(render, variables)
