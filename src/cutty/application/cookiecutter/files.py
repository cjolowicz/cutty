"""File storage for Cookiecutter."""
import pathlib
from collections.abc import Iterable

from cutty.application.cookiecutter.filestorage import cookiecutterfilestorage
from cutty.filestorage.domain.files import File as BaseFile
from cutty.filesystems.domain.purepath import PurePath


class CookiecutterFileStorage:
    """Disk-based file store with pre and post hooks."""

    def __init__(
        self,
        root: pathlib.Path,
        *,
        hooks: Iterable[BaseFile] = (),
        overwrite_if_exists: bool = False,
        skip_if_file_exists: bool = False,
    ) -> None:
        """Initialize."""
        self.root = root
        self.hookfiles = hooks
        self.overwrite_if_exists = overwrite_if_exists
        self.skip_if_file_exists = skip_if_file_exists

    def store(self, files: Iterable[BaseFile]) -> None:
        """Store the files on disk."""
        with cookiecutterfilestorage(
            self.root,
            hookfiles=self.hookfiles,
            overwrite_if_exists=self.overwrite_if_exists,
            skip_if_file_exists=self.skip_if_file_exists,
        ) as storefile:
            for file in files:
                storefile(file)

    def resolve(self, path: PurePath) -> pathlib.Path:
        """Resolve the path to a filesystem location."""
        return self.root.joinpath(*path.parts)
