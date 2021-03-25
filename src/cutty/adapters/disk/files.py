"""Disk-based implementation of cutty.domain.files abstractions."""
from __future__ import annotations

import pathlib
from collections.abc import Iterable

from cutty.domain.files import File
from cutty.domain.files import Mode
from cutty.filesystem.pure import PurePath


class DiskFileStorage:
    """Disk-based store for files."""

    def __init__(self, root: pathlib.Path) -> None:
        """Initialize."""
        self.root = root

    def store(self, files: Iterable[File]) -> None:
        """Commit the files to storage."""
        for file in files:
            path = self.resolve(file.path)
            self.storefile(file, path)

    def storefile(self, file: File, path: pathlib.Path) -> None:
        """Commit a file to storage."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(file.blob)
        if file.mode & Mode.EXECUTABLE:
            path.chmod(path.stat().st_mode | 0o111)

    def resolve(self, path: PurePath) -> pathlib.Path:
        """Resolve the path to a filesystem location."""
        return self.root.joinpath(*path.parts)
