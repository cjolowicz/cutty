"""Template bindings."""
from dataclasses import dataclass
from typing import Generic
from typing import TypeVar
from typing import Union


Value = Union[None, bool, int, float, str, list, dict]
ValueT = TypeVar("ValueT", bound=Value)
ValueT_co = TypeVar("ValueT_co", bound=Value, covariant=True)


@dataclass(frozen=True)
class Binding(Generic[ValueT_co]):
    """A variable binds a name to a value."""

    name: str
    value: ValueT_co
