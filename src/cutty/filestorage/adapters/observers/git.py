"""Storing files in a Git repository."""
import pathlib
from typing import Optional

import pygit2

from cutty.filestorage.domain.observers import FileStorageObserver


LATEST_BRANCH = "cutty/latest"
LATEST_BRANCH_REF = f"refs/heads/{LATEST_BRANCH}"
UPDATE_BRANCH = "cutty/update"
UPDATE_BRANCH_REF = f"refs/heads/{UPDATE_BRANCH}"
CREATE_MESSAGE = "Initial import"
UPDATE_MESSAGE = "Update project template"


def default_signature(repository: pygit2.Repository) -> pygit2.Signature:
    """Return the default signature."""
    from cutty.util.git import default_signature

    return default_signature(repository)


def commit(
    repository: pygit2.Repository,
    *,
    message: str,
    signature: Optional[pygit2.Signature] = None,
) -> None:
    """Commit all changes in the repository.

    If there are no changes relative to the parent, this is a noop.
    """
    from cutty.util.git import commit

    commit(repository, message=message, signature=signature)


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

        if UPDATE_BRANCH in repository.branches:
            # HEAD must point to update branch if it exists.
            head = repository.references["HEAD"].target
            if head != UPDATE_BRANCH_REF:
                raise RuntimeError(f"unexpected HEAD: {head}")

        message = (
            CREATE_MESSAGE
            if LATEST_BRANCH not in repository.branches
            else UPDATE_MESSAGE
        )

        commit(repository, message=message)

        if LATEST_BRANCH not in repository.branches:
            repository.branches.create(LATEST_BRANCH, repository.head.peel())
