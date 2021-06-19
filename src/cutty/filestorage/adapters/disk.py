"""Disk-based file storage."""
import enum
import pathlib
import tempfile
from collections.abc import Callable
from collections.abc import Iterator
from typing import Any
from typing import Optional

from cutty.compat.contextlib import contextmanager
from cutty.filestorage.domain.files import Executable
from cutty.filestorage.domain.files import File
from cutty.filestorage.domain.files import RegularFile
from cutty.filestorage.domain.files import SymbolicLink
from cutty.filestorage.domain.storage import FileStorage
from cutty.filestorage.domain.storage import FileStore


class FileExistsPolicy(enum.Enum):
    """What to do when a file already exists."""

    RAISE = enum.auto()
    OVERWRITE = enum.auto()
    SKIP = enum.auto()


def _storefile(
    file: File,
    path: pathlib.Path,
    *,
    undo: list[Callable[[], None]],
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
            undo.append(parent.rmdir)

    if isinstance(file, RegularFile):
        path.write_bytes(file.blob)

        if not overwrite:
            undo.append(path.unlink)

        if isinstance(file, Executable):
            path.chmod(path.stat().st_mode | 0o111)

    elif isinstance(file, SymbolicLink):
        target = pathlib.Path(*file.target.parts)
        path.symlink_to(target)

        if not overwrite:
            undo.append(path.unlink)

    else:
        raise TypeError(f"cannot store file of type {type(file)}")


def storefile(
    file: File,
    *,
    root: pathlib.Path,
    fileexists: FileExistsPolicy,
    undo: list[Callable[[], None]],
) -> None:
    """Store the file in a directory on disk."""
    path = root.joinpath(*file.path.parts)

    if not path.exists():
        _storefile(file, path, undo=undo)
    elif fileexists is FileExistsPolicy.OVERWRITE:
        _storefile(file, path, undo=undo, overwrite=True)
    elif fileexists is FileExistsPolicy.RAISE:
        raise FileExistsError(f"{path} already exists")


@contextmanager
def diskfilestorage(
    root: pathlib.Path,
    *,
    fileexists: FileExistsPolicy = FileExistsPolicy.RAISE,
) -> Iterator[FileStore]:
    """Disk-based store for files."""
    with DiskFileStorage(root, fileexists=fileexists) as storage:
        yield storage.add


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
        storefile(file, root=self.root, fileexists=self.fileexists, undo=self.undo)

    def rollback(self) -> None:
        """Rollback all stores."""
        for action in reversed(self.undo):
            action()  # if this fails then so be it


class TemporaryDiskFileStorage(DiskFileStorage):
    """Temporary disk-based file storage."""

    def __init__(
        self,
        *,
        fileexists: FileExistsPolicy = FileExistsPolicy.RAISE,
        onstore: Optional[Callable[[pathlib.Path], None]] = None,
    ) -> None:
        """Initialize."""
        # FIXME: fileexists makes no sense for temporary storage
        self._directory = tempfile.TemporaryDirectory()
        self._onstore = onstore
        super().__init__(pathlib.Path(self._directory.name), fileexists=fileexists)

    def add(self, file: File) -> None:
        """Add the file to the storage."""
        super().add(file)
        if self._onstore is not None:
            self._onstore(self.root.joinpath(*file.path.parts))

    def __enter__(self) -> FileStorage:
        """Enter the runtime context."""
        self._directory.__enter__()
        return super().__enter__()

    def __exit__(self, *args: Any) -> None:
        """Exit the runtime context."""
        super().__exit__(*args)
        self._directory.__exit__(*args)


@contextmanager
def temporarydiskfilestorage(
    *,
    fileexists: FileExistsPolicy = FileExistsPolicy.RAISE,
    onstore: Optional[Callable[[pathlib.Path], None]] = None,
) -> Iterator[FileStore]:
    """Temporary disk-based store for files."""
    with TemporaryDiskFileStorage(fileexists=fileexists, onstore=onstore) as storage:
        yield storage.add
