"""General-purpose utilities."""
import contextlib
import os
import shutil
import stat
from pathlib import Path
from typing import Any
from typing import Iterator
from typing import Optional


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
