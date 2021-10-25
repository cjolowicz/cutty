"""Determining storage locations for URLs."""
import pathlib
from collections.abc import Callable

from yarl import URL


Store = Callable[[URL], pathlib.Path]


def defaultstore(url: URL) -> pathlib.Path:
    """Return the relative path to the repository within the storage location."""
    path = pathlib.PurePosixPath(url.path)
    path = path.relative_to(path.parent)
    return pathlib.Path(path)
