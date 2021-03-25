"""Binding variables."""
from collections.abc import Callable
from collections.abc import Sequence

from cutty.domain.bindings import Binding
from cutty.domain.render import Renderer
from cutty.domain.variables import Variable


Binder = Callable[[Variable], Binding]
RenderBinder = Callable[[Renderer, Sequence[Variable]], Sequence[Binding]]


def binddefault(variable: Variable) -> Binding:
    """Bind a variable to its default value."""
    return Binding(variable.name, variable.default)


def renderbind(
    render: Renderer, bind: Binder, variables: Sequence[Variable]
) -> Sequence[Binding]:
    """Successively render and bind variables."""
    bindings: list[Binding] = []
    for variable in variables:
        variable = render(variable, bindings)
        binding = bind(variable)
        bindings.append(binding)
    return bindings


def renderbindwith(bind: Binder) -> RenderBinder:
    """Render and bind variables using the given binder."""
    return lambda render, variables: renderbind(render, bind, variables)
