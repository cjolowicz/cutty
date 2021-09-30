"""Updating projects with changes from their templates."""
from pathlib import Path

from cutty.projects.common import CreateProject2
from cutty.projects.common import LATEST_BRANCH
from cutty.projects.common import UPDATE_BRANCH
from cutty.projects.common import updatecommitmessage
from cutty.services.loadtemplate import Template
from cutty.util.git import Repository


def updateproject(
    projectdir: Path, createproject: CreateProject2, template: Template
) -> None:
    """Update a project by applying changes between the generated trees."""
    project = Repository.open(projectdir)

    latestbranch = project.branch(LATEST_BRANCH)
    updatebranch = project.heads.create(UPDATE_BRANCH, latestbranch.commit, force=True)

    with project.worktree(updatebranch, checkout=False) as worktree:
        createproject(worktree)
        Repository.open(worktree).commit(
            message=updatecommitmessage(template.repository)
        )

    project.cherrypick(updatebranch.commit)

    latestbranch.commit = updatebranch.commit


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
