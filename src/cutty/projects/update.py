"""Updating projects with changes from their templates."""
from pathlib import Path

from cutty.projects.common import LATEST_BRANCH
from cutty.projects.common import UPDATE_BRANCH
from cutty.util.git import Repository


def continueupdate(projectdir: Path) -> None:
    """Continue an update after conflict resolution."""
    project = Repository.open(projectdir)

    if commit := project.cherrypickhead:
        project.commit(
            message=commit.message,
            author=commit.author,
            committer=project.default_signature,
        )

    project.heads[LATEST_BRANCH] = project.heads[UPDATE_BRANCH]


def skipupdate(projectdir: Path) -> None:
    """Skip an update with conflicts."""
    project = Repository.open(projectdir)
    project.resetcherrypick()

    project.heads[LATEST_BRANCH] = project.heads[UPDATE_BRANCH]


def abortupdate(projectdir: Path) -> None:
    """Abort an update with conflicts."""
    project = Repository.open(projectdir)
    project.resetcherrypick()

    project.heads[UPDATE_BRANCH] = project.heads[LATEST_BRANCH]
