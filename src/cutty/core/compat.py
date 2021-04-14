"""Compatibility."""
import contextlib
import sys
from typing import Callable
from typing import ContextManager
from typing import Iterator
from typing import TYPE_CHECKING
from typing import TypeVar


T = TypeVar("T")


if sys.version_info >= (3, 8):
    from functools import cached_property as cached_property
elif TYPE_CHECKING:
    from typing import Any
    from typing import Type

    # fmt: off
    class cached_property:                                                # noqa: D101, N801
        def __init__(self, func: Callable[[Any], T]) -> None: ...         # noqa: D107, E704
        def __set_name__(self, owner: Type[Any], name: str) -> None: ...  # noqa: D105, E704
        def __get__(self, instance: Any, owner: Any = None) -> Any: ...   # noqa: D105, E704
    # fmt: on
else:
    from backports.cached_property import (  # noqa: F401
        cached_property as cached_property,
    )


def contextmanager(
    func: Callable[..., Iterator[T]]
) -> Callable[..., ContextManager[T]]:
    """Fix annotations of functions decorated by contextlib.contextmanager."""
    result = contextlib.contextmanager(func)
    result.__annotations__ = {**func.__annotations__, "return": ContextManager[T]}
    return result
