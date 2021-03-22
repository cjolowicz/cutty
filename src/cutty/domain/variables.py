"""Template variables."""
from dataclasses import dataclass
from typing import Generic

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
