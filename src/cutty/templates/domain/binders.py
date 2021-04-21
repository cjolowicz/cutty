"""Binding variables."""
from collections.abc import Callable
from collections.abc import Sequence
from typing import Any

from cutty.templates.domain.bindings import Binding
from cutty.templates.domain.render import Renderer
from cutty.templates.domain.variables import validate
from cutty.templates.domain.variables import Variable


Binder = Callable[[Variable], Binding]
RenderingBinder = Callable[[Renderer, Sequence[Variable]], Sequence[Binding]]


def bind(variable: Variable, value: Any) -> Binding:
    """Bind a variable to a value."""
    validate(value, variable)
    return Binding(variable.name, value)


def binddefault(variable: Variable) -> Binding:
    """Bind a variable to its default value."""
    return bind(variable, variable.default)


def override(binder: Binder, bindings: Sequence[Binding]) -> Binder:
    """Only use the binder if the binding does not yet exist."""
    if not bindings:
        return binder

    mapping = {binding.name: binding.value for binding in bindings}

    def _binder(variable: Variable) -> Binding:
        try:
            value = mapping[variable.name]
        except KeyError:
            return binder(variable)

        return bind(variable, value)

    return _binder


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
