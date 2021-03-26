"""Repository based on a zip archive."""
from cutty.filesystem.adapters.zip import ZipFilesystem
from cutty.filesystem.domain.path import Path
from cutty.repositories.domain.repositories import LocalRepository


class LocalZipRepository(LocalRepository):
    """Local zip repository."""

    type: str = "zip-local"

    @classmethod
    def supports(cls, path: pathlib.Path) -> bool:
        """Return True if the implementation supports the given path."""
        return path.suffix.lower() == ".zip" and path.is_file()

    def resolve(self, revision: Optional[str]) -> Path:
        """Return a filesystem tree for the given revision."""
        if revision is not None:
            raise RuntimeError(
                f"{self.type} repository does not support revisions, got {revision}"
            )
        return Path(filesystem=ZipFilesystem(self.path))
