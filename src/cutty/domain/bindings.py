"""Bindings."""
from dataclasses import dataclass
from typing import Generic

from cutty.domain.values import Value
from cutty.domain.values import ValueT_co


@dataclass(frozen=True)
class GenericBinding(Generic[ValueT_co]):
    """A binding associates a name with a value."""

    name: str
    value: ValueT_co


Binding = GenericBinding[Value]
