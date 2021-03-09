"""Compatibility shim for contextlib."""
import contextlib
from collections.abc import Callable
from collections.abc import Iterator
from typing import TypeVar


T = TypeVar("T")


def contextmanager(
    func: Callable[..., Iterator[T]]
) -> Callable[..., contextlib.AbstractContextManager[T]]:
    """Fix annotations of functions decorated by contextlib.contextmanager."""
    result = contextlib.contextmanager(func)
    result.__annotations__ = {
        **func.__annotations__,
        "return": contextlib.AbstractContextManager[T],
    }
    return result
