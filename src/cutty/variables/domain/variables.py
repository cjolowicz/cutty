"""Template variables."""
from dataclasses import dataclass
from typing import Any
from typing import Generic
from typing import TypeVar


T_co = TypeVar("T_co", covariant=True)


@dataclass(frozen=True)
class GenericVariable(Generic[T_co]):
    """Template variables are specifications for bindings."""

    name: str
    description: str
    type: type[T_co]
    default: T_co
    choices: tuple[T_co, ...]
    interactive: bool


Variable = GenericVariable[Any]


def validate(value: Any, variable: Variable) -> None:
    """Raise ValueError if the value is not compatible with the variable."""
    if not isinstance(value, variable.type):
        raise ValueError(f"{variable.name} has type {variable.type}, got {value!r}")

    if variable.choices and value not in variable.choices:
        raise ValueError(
            f"{variable.name} has choices {variable.choices}, got {value!r}"
        )
