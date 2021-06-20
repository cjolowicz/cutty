"""Disk-based file storage."""
import enum
import pathlib
from collections.abc import Callable
from typing import Optional

from cutty.filestorage.domain.files import Executable
from cutty.filestorage.domain.files import File
from cutty.filestorage.domain.files import RegularFile
from cutty.filestorage.domain.files import SymbolicLink
from cutty.filestorage.domain.storage import FileStorage


class FileExistsPolicy(enum.Enum):
    """What to do when a file already exists."""

    RAISE = enum.auto()
    OVERWRITE = enum.auto()
    SKIP = enum.auto()


class DiskFileStorage(FileStorage):
    """Disk-based file storage."""

    def __init__(
        self,
        root: pathlib.Path,
        *,
        fileexists: FileExistsPolicy = FileExistsPolicy.RAISE,
    ) -> None:
        """Initialize."""
        self.root = root
        self.fileexists = fileexists
        self.undo: list[Callable[[], None]] = []

    def add(self, file: File) -> None:
        """Add the file to the storage."""
        path = self.resolve(file)
        overwrite = self.checkpolicy(path)

        if overwrite is not None:
            self._storefile(file, path, overwrite=overwrite)

    def resolve(self, file: File) -> pathlib.Path:
        """Return the filesystem location."""
        return self.root.joinpath(*file.path.parts)

    def checkpolicy(self, path: pathlib.Path) -> Optional[bool]:
        """Check the policy for existing files."""
        if not path.exists():
            return False

        if self.fileexists is FileExistsPolicy.OVERWRITE:
            return True

        if self.fileexists is FileExistsPolicy.RAISE:
            raise FileExistsError(f"{path} already exists")

        assert self.fileexists is FileExistsPolicy.SKIP  # noqa: S101
        return None

    def _storefile(
        self,
        file: File,
        path: pathlib.Path,
        *,
        overwrite: bool = False,
    ) -> None:
        """Store the file at the given path on disk."""
        # OVERWRITING.
        #
        # These operations are allowed:
        #
        # - Overwrite a regular file with another regular file.
        # - Overwrite a symbolic link with a regular file.
        # - Overwrite a symbolic link with another symbolic link.
        #
        # These operations raise exceptions:
        #
        # - Do not overwrite a directory with a regular file.
        # - Do not overwrite a directory with a symbolic link.
        # - Do not overwrite a regular file with a symbolic link.
        # - Do not overwrite a regular file with a directory.
        # - Do not overwrite a symbolic link with a directory if the link target is
        #   not a directory. (Symbolic links in the path are followed if they point
        #   to directories.)

        if overwrite and path.is_symlink():
            path.unlink()

        for parent in reversed(path.parents):
            if not parent.is_dir():
                parent.mkdir()
                self.undo.append(parent.rmdir)

        if isinstance(file, RegularFile):
            path.write_bytes(file.blob)

            if not overwrite:
                self.undo.append(path.unlink)

            if isinstance(file, Executable):
                path.chmod(path.stat().st_mode | 0o111)

        elif isinstance(file, SymbolicLink):
            target = pathlib.Path(*file.target.parts)
            path.symlink_to(target)

            if not overwrite:
                self.undo.append(path.unlink)

        else:
            raise TypeError(f"cannot store file of type {type(file)}")

    def rollback(self) -> None:
        """Rollback all stores."""
        for action in reversed(self.undo):
            action()  # if this fails then so be it
