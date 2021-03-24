"""Repositories."""
from __future__ import annotations

import abc
import pathlib
import shutil
from typing import Optional

from yarl import URL

from cutty.filesystem.path import Path


class Repository(abc.ABC):
    """Abstract base class for a repository."""

    type: str

    def __init__(self, url: URL, path: pathlib.Path) -> None:
        """Initialize."""
        self.url = url
        self.path = path

    @classmethod
    @abc.abstractmethod
    def matches(cls, url: URL) -> bool:
        """Return True if the provider handles the given URL."""

    @abc.abstractmethod
    def exists(self) -> bool:
        """Return True if the repository exists."""

    @abc.abstractmethod
    def download(self) -> None:
        """Download the repository to the given path."""

    def update(self) -> None:
        """Update the repository at the given path."""
        shutil.rmtree(self.path)
        self.download()

    @abc.abstractmethod
    def resolve(self, revision: Optional[str]) -> Path:
        """Return a filesystem tree for the given revision."""
