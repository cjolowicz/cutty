"""Disk-based backend."""
import hashlib
import pathlib
from collections.abc import Callable

from cutty.filesystem.disk import DiskFilesystem
from cutty.filesystem.path import Path


def _hash(value: str) -> str:
    return hashlib.blake2b(value.encode()).hexdigest()


def createbackend(root: pathlib.Path) -> Callable[[str], Path]:
    """Create a backend."""

    def locate(url: str) -> Path:
        """Locate storage for the URL."""
        hash = _hash(url)
        path = root / "repositories" / hash[:2] / hash
        path.mkdir(parents=True, exist_ok=True)
        return Path(filesystem=DiskFilesystem(path))

    root.mkdir(parents=True, exist_ok=True)
    return locate
