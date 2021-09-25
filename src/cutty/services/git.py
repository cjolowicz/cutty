"""Storing files in a Git repository."""
import pathlib
from typing import Optional

import pygit2

from cutty.util.git import Repository


LATEST_BRANCH = "cutty/latest"
UPDATE_BRANCH = "cutty/update"


def creategitrepository(
    project: pathlib.Path, template: str, revision: Optional[str]
) -> None:
    """Create a git repository."""
    try:
        repository = Repository.open(project)
    except pygit2.GitError:
        repository = Repository.init(project)

    if UPDATE_BRANCH in repository.heads:
        # HEAD must point to update branch if it exists.
        head = repository.head.name
        if head != UPDATE_BRANCH:
            raise RuntimeError(f"unexpected HEAD: {head}")

    update = LATEST_BRANCH in repository.heads

    if update and revision:
        message = f"Update {template} to {revision}"
    elif update:
        message = f"Update {template}"
    elif revision:
        message = f"Initial import from {template} {revision}"
    else:
        message = f"Initial import from {template}"

    repository.commit(message=message)
    repository.heads.setdefault(LATEST_BRANCH, repository.head.commit)
