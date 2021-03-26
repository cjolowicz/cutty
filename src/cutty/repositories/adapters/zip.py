"""Repository based on a zip archive."""
import pathlib
import shutil
import urllib.request
from typing import Optional

import httpx
from yarl import URL

from cutty.filesystems.adapters.zip import ZipFilesystem
from cutty.repositories.domain.repositories import LocalRepository
from cutty.repositories.domain.repositories import Repository


class LocalZipRepository(LocalRepository):
    """Repository for a local ZIP archive."""

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


def download(url: URL, path: pathlib.Path) -> None:
    """Download the URL to the given path."""
    if not url.scheme or url.scheme == "file":
        shutil.copyfile(url.path, path)

    elif url.scheme in ["http", "https"]:
        with httpx.stream("GET", str(url)) as response:
            response.raise_for_status()
            with path.open(mode="wb") as io:
                for data in response.iter_bytes():
                    io.write(data)

    elif url.scheme == "ftp":
        with urllib.request.urlopen(str(url)) as response:  # noqa: S310
            status: int = response.status  # type: ignore[attr-defined]
            if 400 <= status <= 599:
                raise RuntimeError(f"download failed: {url}: {status}")
            with path.open(mode="wb") as io:
                shutil.copyfileobj(response, io)  # type: ignore[arg-type]


class ZipRepository(Repository):
    """Repository for a remote ZIP archive."""

    type: str = "zip"
    schemes = {"file", "ftp", "http", "https"}

    @property
    def repositorypath(self) -> pathlib.Path:
        """Return the location of the ZIP archive."""
        remotepath = pathlib.PurePosixPath(self.url.path)
        return self.path / remotepath.name

    @classmethod
    def supports(cls, url: URL) -> bool:
        """Return True if the implementation supports the given URL."""
        return url.path.lower().endswith(".zip") and (
            not url.scheme or url.scheme in cls.schemes
        )

    def exists(self) -> bool:
        """Return True if the repository exists."""
        return self.repositorypath.exists()

    def download(self) -> None:
        """Download the repository to the given path."""
        download(self.url, self.repositorypath)

    def update(self) -> None:
        """Update the repository at the given path."""
        self.repositorypath.unlink()
        self.download()

    def resolve(self, revision: Optional[str]) -> ZipFilesystem:
        """Return a filesystem for the given revision."""
        if revision is not None:
            raise RuntimeError(
                f"{self.type} repository does not support revisions, got {revision}"
            )
        return ZipFilesystem(self.repositorypath)
