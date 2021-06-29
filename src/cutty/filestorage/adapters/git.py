"""Storing files in a Git repository."""
import contextlib
import os
import pathlib
from typing import Optional

import pygit2

from cutty.filestorage.domain.files import File
from cutty.filestorage.domain.storage import FileStorageObserver


def default_signature(repository: pygit2.Repository) -> pygit2.Signature:
    """Return the default signature."""
    with contextlib.suppress(KeyError):
        return pygit2.Signature(
            os.environ["GIT_AUTHOR_NAME"],
            os.environ["GIT_AUTHOR_EMAIL"],
        )
    return repository.default_signature  # pragma: no cover


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
        self.repository.index.write()
        signature = default_signature(self.repository)
        self.repository.create_commit("HEAD", signature, signature, "Initial", tree, [])
