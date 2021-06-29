"""Storing files in a Git repository."""
import pathlib
from typing import Optional

import pygit2

from cutty.filestorage.domain.files import File
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

    def add(self, file: File) -> None:
        """A file was added to the transaction."""
        path = "/".join(file.path.parts[1:])
        assert self.repository is not None  # noqa: S101
        self.repository.index.add(path)

    def commit(self) -> None:
        """A storage transaction was completed."""
        assert self.repository is not None  # noqa: S101
        tree = self.repository.index.write_tree()
        self.repository.create_commit(
            "HEAD",
            self.repository.default_signature,
            self.repository.default_signature,
            "Initial",
            tree,
            [],
        )
