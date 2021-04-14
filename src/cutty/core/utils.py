"""General-purpose utilities."""
import collections.abc
import contextlib
import functools
import importlib
import os
import shutil
import stat
from pathlib import Path
from typing import Any
from typing import Callable
from typing import ContextManager
from typing import Iterable
from typing import Iterator
from typing import List
from typing import Optional
from typing import TypeVar
from typing import Union

from .compat import contextmanager
from .types import AbstractContextManager


def as_optional_path(argument: Optional[str]) -> Optional[Path]:
    """Convert the argument to a Path if it is not None."""
    return Path(argument) if argument is not None else None


def removeprefix(string: str, prefix: str) -> str:
    """Remove prefix from string, if present."""
    return string[len(prefix) :] if string.startswith(prefix) else string


def rmtree(path: Path) -> None:
    """Remove a directory tree.

    On Windows, read-only files cannot be removed. Use the `onerror` callback
    to clear the read-only bit and retry.

    See https://docs.python.org/3/library/shutil.html#rmtree-example
    """

    def _onerror(function: Any, path: Any, excinfo: Any) -> Any:
        os.chmod(path, stat.S_IWRITE)
        function(path)

    shutil.rmtree(path, onerror=_onerror)


class OnRaise(AbstractContextManager):
    """Invoke a callback when leaving the context due to an exception."""

    def __init__(self, callback: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        """Initialize."""
        self._args = (callback, args, kwargs)

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        """Exit the context."""
        if exc_type is not None:
            (callback, args, kwargs) = self._args
            callback(*args, **kwargs)


on_raise = OnRaise


def make_executable(path: Path) -> None:
    """Set the executable bit on a file."""
    status = os.stat(path)
    os.chmod(path, status.st_mode | stat.S_IEXEC)


@contextmanager
def multicontext(contexts: Iterable[ContextManager[Any]]) -> Iterator[List[Any]]:
    """Group multiple context managers in a single context manager."""
    with contextlib.ExitStack() as stack:
        yield [stack.enter_context(context) for context in contexts]


R = TypeVar("R")


def with_context(
    contextfactory: Callable[
        ..., Union[ContextManager[Any], Iterable[ContextManager[Any]]]
    ]
) -> Callable[[Callable[..., R]], Callable[..., R]]:
    """Invoke a function with a context manager created at call time."""

    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> R:
            context = contextfactory(*args, **kwargs)
            if isinstance(context, collections.abc.Iterable):
                context = multicontext(context)
            with context:
                return func(*args, **kwargs)

        return wrapper

    return decorator


def import_object(import_path: str) -> Any:
    """Import the object at the given import path.

    Import paths consist of the dotted module name, optionally followed by a
    colon or dot, and the module attribute at which the object is located.

    For example:

    - ``json``
    - ``os.path``
    - ``xml.sax.saxutils:escape``
    - ``xml.sax.saxutils.escape``

    This function mirrors the implementation of ``jinja2.utils.import_string``.
    """
    module_name, colon, attribute = import_path.rpartition(":")

    if not colon:
        module_name, _, attribute = import_path.rpartition(".")

    module = importlib.import_module(module_name)
    return getattr(module, attribute) if attribute else module
