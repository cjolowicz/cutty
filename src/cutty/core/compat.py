"""Compatibility."""
import contextlib
from typing import Callable
from typing import ContextManager
from typing import Iterator
from typing import TypeVar

from backports import cached_property as cached_property  # noqa: F401


T = TypeVar("T")


def contextmanager(
    func: Callable[..., Iterator[T]]
) -> Callable[..., ContextManager[T]]:
    """Fix annotations of functions decorated by contextlib.contextmanager."""
    result = contextlib.contextmanager(func)
    result.__annotations__ = {**func.__annotations__, "return": ContextManager[T]}
    return result
