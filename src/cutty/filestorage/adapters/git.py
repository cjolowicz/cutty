"""Storing files in a Git repository."""
import pathlib

import pygit2

from cutty.filestorage.domain.storage import FileStorageObserver


class GitRepositoryObserver(FileStorageObserver):
    """Storage observer creating a git repository."""

    def __init__(self, *, project: pathlib.Path) -> None:
        """Initialize."""
        self.project = project

    def commit(self) -> None:
        """A storage transaction was completed."""
        pygit2.init_repository(self.project)
