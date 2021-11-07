"""Bindings."""
from dataclasses import dataclass
from typing import Any
from typing import Generic
from typing import TypeVar


T_co = TypeVar("T_co", covariant=True)


@dataclass(frozen=True)
class GenericBinding(Generic[T_co]):
    """A binding associates a name with a value."""

    name: str
    value: T_co


Binding = GenericBinding[Any]
