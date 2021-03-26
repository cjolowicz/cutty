"""Filesystem implementation for ZIP archives using zipfile."""
import pathlib
import stat
import zipfile
from collections.abc import Iterator

from cutty.filesystem.domain.base import Access
from cutty.filesystem.domain.base import Filesystem
from cutty.filesystem.domain.pure import PurePath


def _fromaccess(access: Access) -> int:
    mapping = {
        Access.READ: stat.S_IRUSR,
        Access.WRITE: stat.S_IWUSR,
        Access.EXECUTE: stat.S_IXUSR,
    }
    return sum(mapping[flag] for flag in Access if flag in access)


def _getfilemode(zippath: zipfile.Path) -> int:
    info: zipfile.ZipInfo
    info = zippath.root.getinfo(zippath.at)  # type: ignore[attr-defined]
    return info.external_attr >> 16


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
        zippath = self.resolve(path)
        return (
            bool(_getfilemode(zippath) & _fromaccess(mode))
            if mode
            else zippath.exists()
        )
