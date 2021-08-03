"""Storing files in a Git repository."""
import pathlib

import pygit2

from cutty.filestorage.domain.observers import FileStorageObserver
from cutty.util.git import Repository


LATEST_BRANCH = "cutty/latest"
UPDATE_BRANCH = "cutty/update"
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

        if UPDATE_BRANCH in repository.heads:
            # HEAD must point to update branch if it exists.
            head = repository.head.name
            if head != UPDATE_BRANCH:
                raise RuntimeError(f"unexpected HEAD: {head}")

        message = (
            CREATE_MESSAGE if LATEST_BRANCH not in repository.heads else UPDATE_MESSAGE
        )

        repository.commit(message=message)

        repository.heads.setdefault(LATEST_BRANCH, repository.head.commit)
