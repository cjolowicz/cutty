"""Values."""
from enum import Enum
from typing import Any
from typing import TypeVar
from typing import Union


Value = Union[bool, int, float, str, list, dict]
ValueT = TypeVar("ValueT", bound=Value)
ValueT_co = TypeVar("ValueT_co", bound=Value, covariant=True)


class ValueType(str, Enum):
    """The kinds of values a template variable can hold."""

    BOOLEAN = "boolean"
    NUMBER = "number"
    STRING = "string"
    ARRAY = "array"
    OBJECT = "object"


def getvaluetype(value: Any) -> ValueType:
    """Return the appropriate value type for the value."""
    mapping = {
        bool: ValueType.BOOLEAN,
        int: ValueType.NUMBER,
        float: ValueType.NUMBER,
        str: ValueType.STRING,
        list: ValueType.ARRAY,
        dict: ValueType.OBJECT,
    }

    for cls, valuetype in mapping.items():
        if isinstance(value, cls):
            return valuetype

    raise RuntimeError(f"unsupported value type {type(value)}")  # pragma: no cover
