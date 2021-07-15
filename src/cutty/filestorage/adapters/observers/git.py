"""Storing files in a Git repository."""
import contextlib
import os
import pathlib

import pygit2

from cutty.filestorage.domain.observers import FileStorageObserver


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

    def commit(self) -> None:
        """A storage transaction was completed."""
        if pygit2.discover_repository(self.project, False, self.project.parent):
            # Do nothing if there's already a repository.
            return

        repository = pygit2.init_repository(self.project)
        repository.index.add_all()
        tree = repository.index.write_tree()
        repository.index.write()
        signature = default_signature(repository)
        repository.create_commit("HEAD", signature, signature, "Initial", tree, [])
        repository.branches.create("cutty/latest", repository.head.peel())
