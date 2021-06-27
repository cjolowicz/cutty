"""The peek utility."""
import itertools
from collections.abc import Iterable
from collections.abc import Iterator
from typing import Optional
from typing import TypeVar

T = TypeVar("T")


def peek(
    iterable: Iterable[T], *, default: Optional[T] = None
) -> tuple[Optional[T], Iterator[T]]:
    """Peek at the first item of an iterable."""
    iterator = iter(iterable)
    try:
        first = next(iterator)
    except StopIteration:
        return default, iterator
    else:
        return first, itertools.chain([first], iterator)
