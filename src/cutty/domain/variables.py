"""Template variables."""
from dataclasses import dataclass
from typing import Generic

from cutty.domain.values import getvaluetype
from cutty.domain.values import Value
from cutty.domain.values import ValueT_co
from cutty.domain.values import ValueType


@dataclass(frozen=True)
class GenericVariable(Generic[ValueT_co]):
    """Template variables are specifications for bindings."""

    name: str
    description: str
    type: ValueType
    default: ValueT_co
    choices: tuple[ValueT_co, ...]
    interactive: bool


Variable = GenericVariable[Value]


def validate(value: Value, variable: Variable) -> None:
    """Raise ValueError if the value is not compatible with the variable."""
    if getvaluetype(value) != variable.type:
        raise ValueError(f"{variable.name} has type {variable.type}, got {value!r}")

    if variable.choices and value not in variable.choices:
        raise ValueError(
            f"{variable.name} has choices {variable.choices}, got {value!r}"
        )
