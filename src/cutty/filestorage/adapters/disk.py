"""Disk-based file storage."""
import contextlib
import enum
import pathlib
from collections.abc import Callable
from typing import Optional

from cutty.filestorage.domain.files import Executable
from cutty.filestorage.domain.files import File
from cutty.filestorage.domain.files import RegularFile
from cutty.filestorage.domain.files import SymbolicLink
from cutty.filestorage.domain.storage import FileStorage
from cutty.filesystems.domain.purepath import PurePath


class FileExistsPolicy(enum.Enum):
    """What to do when a file already exists."""

    RAISE = enum.auto()
    OVERWRITE = enum.auto()
    SKIP = enum.auto()

    def check(self, path: pathlib.Path) -> Optional[bool]:
        """Check the policy for a given path.

        Args:
            path: The path to be checked against the policy.

        Returns:
            ``True`` to overwrite the path, ``False`` to skip the path.

        Raises:
            FileExistsError: The policy does not permit overwriting the path.
        """
        if self is FileExistsPolicy.RAISE:
            raise FileExistsError(f"{path} already exists")

        return self is FileExistsPolicy.OVERWRITE


class DiskFileStorage(FileStorage):
    """Disk-based file storage."""

    def __init__(
        self,
        root: pathlib.Path,
        *,
        fileexists: FileExistsPolicy = FileExistsPolicy.RAISE,
    ) -> None:
        """Initialize."""
        super().__init__()
        self.root = root
        self.fileexists = fileexists
        self.undo: list[Callable[[], None]] = []

    def begin(self) -> None:
        """Begin a storage transaction."""

    def add(self, file: File) -> None:
        """Add the file to the storage."""
        path = self.resolve(file.path)
        if not path.exists():
            self._storefile(file, path, overwrite=False)
        elif self.fileexists.check(path):
            self._storefile(file, path, overwrite=True)

    def resolve(self, path: PurePath) -> pathlib.Path:
        """Return the filesystem location."""
        return self.root.joinpath(*path.parts)

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

    def commit(self) -> None:
        """Commit all stores."""

    def rollback(self) -> None:
        """Rollback all stores."""
        for action in reversed(self.undo):
            with contextlib.suppress(Exception):
                action()
