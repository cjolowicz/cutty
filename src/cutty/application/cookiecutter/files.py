"""File storage for Cookiecutter."""
import pathlib
from collections.abc import Iterable

from cutty.application.cookiecutter.filestorage import cookiecutterfilestorage
from cutty.filestorage.domain.files import Executable
from cutty.filestorage.domain.files import File as BaseFile
from cutty.filestorage.domain.files import RegularFile
from cutty.filesystems.domain.purepath import PurePath
from cutty.templates.domain.files import File
from cutty.templates.domain.files import Mode


def _convert_file_representation(file: File) -> BaseFile:
    if Mode.EXECUTABLE in file.mode:
        return Executable(file.path, file.blob)
    return RegularFile(file.path, file.blob)


class CookiecutterFileStorage:
    """Disk-based file store with pre and post hooks."""

    def __init__(
        self,
        root: pathlib.Path,
        *,
        hooks: Iterable[File] = (),
        overwrite_if_exists: bool = False,
        skip_if_file_exists: bool = False,
    ) -> None:
        """Initialize."""
        self.root = root
        self.hookfiles = tuple(_convert_file_representation(hook) for hook in hooks)
        self.overwrite_if_exists = overwrite_if_exists
        self.skip_if_file_exists = skip_if_file_exists

    def store(self, files: Iterable[File]) -> None:
        """Store the files on disk."""
        with cookiecutterfilestorage(
            self.root,
            hookfiles=self.hookfiles,
            overwrite_if_exists=self.overwrite_if_exists,
            skip_if_file_exists=self.skip_if_file_exists,
        ) as storefile:
            for file in files:
                storefile(_convert_file_representation(file))

    def resolve(self, path: PurePath) -> pathlib.Path:
        """Resolve the path to a filesystem location."""
        return self.root.joinpath(*path.parts)
