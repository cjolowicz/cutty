"""Storing files in a Git repository."""
import pathlib
from typing import Optional

import pygit2

from cutty.filestorage.domain.storage import FileStorageObserver


class GitRepositoryObserver(FileStorageObserver):
    """Storage observer creating a git repository."""

    def __init__(self, *, project: pathlib.Path) -> None:
        """Initialize."""
        self.project = project
        self.repository: Optional[pygit2.Repository] = None

    def begin(self) -> None:
        """A storage transaction was started."""
        self.repository = pygit2.init_repository(self.project)
