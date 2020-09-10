"""General-purpose utilities."""
import contextlib
import os
import shutil
import stat
from pathlib import Path
from typing import Any
from typing import Callable
from typing import cast
from typing import ContextManager
from typing import Iterable
from typing import Iterator
from typing import Optional
from typing import TypeVar
from typing import Union


def as_optional_path(argument: Optional[str]) -> Optional[Path]:
    """Convert the argument to a Path if it is not None."""
    return Path(argument) if argument is not None else None


def removeprefix(string: str, prefix: str) -> str:
    """Remove prefix from string, if present."""
    return string[len(prefix) :] if string.startswith(prefix) else string


@contextlib.contextmanager
def chdir(path: Path) -> Iterator[None]:
    """Context manager for changing the directory."""
    cwd = Path.cwd()
    os.chdir(path)

    try:
        yield
    finally:
        os.chdir(cwd)


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


class RemoveTree:
    """Remove a directory tree on exit, unless it already existed."""

    def __init__(self, path: Path) -> None:
        """Initialize."""
        self.stack = contextlib.ExitStack()
        if not path.exists():
            self.stack.callback(rmtree, path)

    def __enter__(self) -> Any:
        """Enter the context."""
        self.stack.__enter__()
        return self

    def __exit__(self, *args: Any) -> None:
        """Exit the context."""
        self.stack.__exit__(*args)

    def cancel(self) -> None:
        """Do not remove the directory tree."""
        self.stack.pop_all()


def make_executable(path: Path) -> None:
    """Set the executable bit on a file."""
    status = os.stat(path)
    os.chmod(path, status.st_mode | stat.S_IEXEC)


def to_context(
    contexts: Union[ContextManager[Any], Iterable[ContextManager[Any]]]
) -> ContextManager[Any]:
    """Return a single context manager."""
    if hasattr(contexts, "__enter__"):
        return cast(ContextManager[Any], contexts)

    stack = contextlib.ExitStack()
    for context in cast(Iterable[ContextManager[Any]], contexts):
        stack.enter_context(context)
    return stack


R = TypeVar("R")


def with_context(
    contextfactory: Callable[
        ..., Union[ContextManager[Any], Iterable[ContextManager[Any]]]
    ]
) -> Callable[[Callable[..., R]], Callable[..., R]]:
    """Invoke a function with a context manager created at call time."""

    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        def wrapper(*args: Any, **kwargs: Any) -> R:
            context = contextfactory(*args, **kwargs)
            context = to_context(context)
            with context:
                return func(*args, **kwargs)

        return wrapper

    return decorator
