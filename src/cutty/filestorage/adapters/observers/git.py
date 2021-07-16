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
        try:
            repository = pygit2.Repository(self.project)
        except pygit2.GitError:
            repository = pygit2.init_repository(self.project)

        repository.index.add_all()
        tree = repository.index.write_tree()
        repository.index.write()
        signature = default_signature(repository)
        parents = [] if repository.head_is_unborn else [repository.head.target]
        repository.create_commit("HEAD", signature, signature, "Initial", tree, parents)

        if "cutty/latest" not in repository.branches:
            repository.branches.create("cutty/latest", repository.head.peel())
        else:
            # HEAD must point to `cutty/latest` if that branch exists.
            head = repository.references["HEAD"].target
            if head != "refs/heads/cutty/latest":
                raise RuntimeError(f"unexpected HEAD: {head}")
