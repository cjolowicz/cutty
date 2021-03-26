"""Filesystem implementation for ZIP archives using zipfile."""
import pathlib
import zipfile
from collections.abc import Iterator

from cutty.filesystem.domain.base import Access
from cutty.filesystem.domain.base import Filesystem
from cutty.filesystem.domain.pure import PurePath


class ZipFilesystem(Filesystem):
    """ZIP filesystem."""

    def __init__(self, path: pathlib.Path) -> None:
        """Inititalize."""
        self._root = zipfile.Path(path)

    def resolve(self, path: PurePath) -> zipfile.Path:
        """Resolve the given path."""
        return self._root.joinpath(*path.parts)

    def is_dir(self, path: PurePath) -> bool:
        """Return True if this is a directory."""
        return self.resolve(path).is_dir()

    def iterdir(self, path: PurePath) -> Iterator[PurePath]:
        """Iterate over the files in this directory."""
        for child in self.resolve(path).iterdir():
            parts = pathlib.PurePosixPath(child.at).parts  # type: ignore[attr-defined]
            yield PurePath(*parts)

    def is_file(self, path: PurePath) -> bool:
        """Return True if this is a regular file (or a symlink to one)."""
        return self.resolve(path).is_file()

    def read_text(self, path: PurePath) -> str:
        """Return the contents of this file."""
        return self.resolve(path).read_text()

    def is_symlink(self, path: PurePath) -> bool:
        """Return True if this is a symbolic link."""
        return False

    def readlink(self, path: PurePath) -> PurePath:
        """Return the target of a symbolic link."""
        raise ValueError(f"{path} is not a symlink")

    def access(self, path: PurePath, mode: Access) -> bool:
        """Return True if the user can access the path."""
        import stat

        if Access.EXECUTE in mode:
            name = self.resolve(path).at  # type: ignore[attr-defined]
            info: zipfile.ZipInfo
            info = self._root.root.getinfo(name)  # type: ignore[attr-defined]
            filemode = info.external_attr >> 16
            return bool(filemode & stat.S_IXUSR)

        return False
