"""Storing files in a Git repository."""
import pathlib
from typing import Optional

import pygit2

from cutty.filestorage.domain.observers import FileStorageObserver
from cutty.util.git import Repository


LATEST_BRANCH = "cutty/latest"
UPDATE_BRANCH = "cutty/update"


class GitRepositoryObserver(FileStorageObserver):
    """Storage observer creating a git repository."""

    def __init__(
        self,
        *,
        project: pathlib.Path,
        template: str = "template",
        revision: Optional[str] = None,
    ) -> None:
        """Initialize."""
        self.project = project
        self.template = template
        self.revision = revision

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

        message = _commitmessage(
            self, self.revision, update=LATEST_BRANCH in repository.heads
        )

        repository.commit(message=message)
        repository.heads.setdefault(LATEST_BRANCH, repository.head.commit)


def _commitmessage(
    self: GitRepositoryObserver, revision: Optional[str], update: bool
) -> str:
    if update and revision:
        return f"Update {self.template} to {revision}"

    if update:
        return f"Update {self.template}"

    if revision:
        return f"Initial import from {self.template} {revision}"

    return f"Initial import from {self.template}"
