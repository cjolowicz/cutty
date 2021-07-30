"""Storing files in a Git repository."""
import pathlib

import pygit2

from cutty.filestorage.domain.observers import FileStorageObserver
from cutty.util.git import Repository


LATEST_BRANCH = "cutty/latest"
LATEST_BRANCH_REF = f"refs/heads/{LATEST_BRANCH}"
UPDATE_BRANCH = "cutty/update"
UPDATE_BRANCH_REF = f"refs/heads/{UPDATE_BRANCH}"
CREATE_MESSAGE = "Initial import"
UPDATE_MESSAGE = "Update project template"


class GitRepositoryObserver(FileStorageObserver):
    """Storage observer creating a git repository."""

    def __init__(self, *, project: pathlib.Path) -> None:
        """Initialize."""
        self.project = project

    def commit(self) -> None:
        """A storage transaction was completed."""
        try:
            repository = Repository.open(self.project)
        except pygit2.GitError:
            repository = Repository.init(self.project)

        if UPDATE_BRANCH in repository.repository.branches:
            # HEAD must point to update branch if it exists.
            head = repository.repository.references["HEAD"].target
            if head != UPDATE_BRANCH_REF:
                raise RuntimeError(f"unexpected HEAD: {head}")

        message = (
            CREATE_MESSAGE
            if LATEST_BRANCH not in repository.repository.branches
            else UPDATE_MESSAGE
        )

        repository.commit(message=message)

        if LATEST_BRANCH not in repository.repository.branches:
            repository.repository.branches.create(
                LATEST_BRANCH, repository.repository.head.peel()
            )
