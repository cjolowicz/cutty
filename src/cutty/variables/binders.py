"""Binding variables."""
from collections.abc import Callable
from collections.abc import Sequence
from typing import Any

from cutty.variables.domain.bindings import Binding
from cutty.variables.domain.variables import validate
from cutty.variables.domain.variables import Variable


Binder = Callable[[Variable], Binding]


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
