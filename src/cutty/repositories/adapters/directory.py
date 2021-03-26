"""Local directory."""
import pathlib
from typing import Optional

from cutty.filesystem.adapters.disk import DiskFilesystem
from cutty.filesystem.domain.path import Path
from cutty.repositories.domain.repositories import LocalRepository


class LocalDirectoryRepository(LocalRepository):
    """Local directory."""

    type: str = "dir-local"

    @classmethod
    def supports(cls, path: pathlib.Path) -> bool:
        """Return True if the implementation supports the given path."""
        return path.is_dir()

    def resolve(self, revision: Optional[str]) -> Path:
        """Return a filesystem tree for the given revision."""
        if revision is not None:
            raise RuntimeError(
                f"{self.type} repository does not support revisions, got {revision}"
            )
        return Path(filesystem=DiskFilesystem(self.path))
