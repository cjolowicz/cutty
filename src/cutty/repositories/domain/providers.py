"""Repository providers."""
import abc
import pathlib
import shutil
from typing import Optional

from yarl import URL

from cutty.filesystem.path import Path


class Provider(abc.ABC):
    """Abstract base class for a repository provider."""

    name: str

    @abc.abstractmethod
    def matches(self, url: URL) -> bool:
        """Return True if the provider handles the given URL."""

    @abc.abstractmethod
    def download(self, url: URL, path: pathlib.Path) -> None:
        """Download the repository to the given path."""

    def update(self, url: URL, path: pathlib.Path) -> None:
        """Update the repository at the given path."""
        shutil.rmtree(path)
        self.download(url, path)

    @abc.abstractmethod
    def resolve(self, path: pathlib.Path, revision: Optional[str]) -> Path:
        """Return a filesystem tree for the given revision."""
