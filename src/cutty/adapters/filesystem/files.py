"""Filesystem implementation of the cutty.domain.files abstractions."""
import pathlib
import tempfile
from collections.abc import Iterator

from cutty.compat.contextlib import contextmanager
from cutty.domain.files import File
from cutty.domain.files import Mode
from cutty.filesystem.pure import PurePath


class FilesystemFileStorage:
    """Filesystem-based store for files."""

    def __init__(self, root: pathlib.Path) -> None:
        """Initialize."""
        self.root = root

    def store(self, file: File) -> None:
        """Commit a file to storage."""
        path = self.resolve(file.path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(file.blob)
        if file.mode & Mode.EXECUTABLE:
            path.chmod(path.stat().st_mode | 0o111)

    def resolve(self, path: PurePath) -> pathlib.Path:
        """Resolve the path to a filesystem location."""
        return self.root.joinpath(*path.parts)

    @classmethod
    @contextmanager
    def temporary(cls) -> Iterator[FilesystemFileStorage]:
        """Return temporary storage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = pathlib.Path(tmpdir)
            yield cls(path)
