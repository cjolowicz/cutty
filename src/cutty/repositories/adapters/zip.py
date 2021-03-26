"""Repository based on a zip archive."""
import pathlib
from typing import Optional

from cutty.filesystems.adapters.zip import ZipFilesystem
from cutty.repositories.domain.repositories import LocalRepository


class LocalZipRepository(LocalRepository):
    """Local zip repository."""

    type: str = "zip-local"

    @classmethod
    def supports(cls, path: pathlib.Path) -> bool:
        """Return True if the implementation supports the given path."""
        return path.suffix.lower() == ".zip" and path.is_file()

    def resolve(self, revision: Optional[str]) -> ZipFilesystem:
        """Return a filesystem tree for the given revision."""
        if revision is not None:
            raise RuntimeError(
                f"{self.type} repository does not support revisions, got {revision}"
            )
        return ZipFilesystem(self.path)
