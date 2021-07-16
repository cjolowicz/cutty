"""Storing files in a Git repository."""
import contextlib
import os
import pathlib
from typing import Optional

import pygit2

from cutty.filestorage.domain.observers import FileStorageObserver


LATEST_BRANCH = "cutty/latest"


def default_signature(repository: pygit2.Repository) -> pygit2.Signature:
    """Return the default signature."""
    with contextlib.suppress(KeyError):
        return pygit2.Signature(
            os.environ["GIT_AUTHOR_NAME"],
            os.environ["GIT_AUTHOR_EMAIL"],
        )
    return repository.default_signature  # pragma: no cover


def commit(
    repository: pygit2.Repository,
    *,
    message: str,
    signature: Optional[pygit2.Signature] = None,
) -> None:
    """Commit all changes in the repository."""
    repository.index.add_all()
    tree = repository.index.write_tree()
    repository.index.write()

    if signature is None:
        signature = default_signature(repository)

    parents = [] if repository.head_is_unborn else [repository.head.target]
    repository.create_commit("HEAD", signature, signature, message, tree, parents)


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

        if LATEST_BRANCH in repository.branches:
            # HEAD must point to latest branch if it exists.
            head = repository.references["HEAD"].target
            if head != f"refs/heads/{LATEST_BRANCH}":
                raise RuntimeError(f"unexpected HEAD: {head}")

        commit(repository, message="Initial")

        if LATEST_BRANCH not in repository.branches:
            repository.branches.create(LATEST_BRANCH, repository.head.peel())
