"""Updating projects with changes from their templates."""
from pathlib import Path

from cutty.projects.create import CreateProject
from cutty.projects.create import LATEST_BRANCH
from cutty.projects.create import UPDATE_BRANCH
from cutty.repositories.domain.repository import Repository as Template
from cutty.util.git import Repository


def updateproject(projectdir: Path, createproject: CreateProject) -> None:
    """Update a project by applying changes between the generated trees."""
    project = Repository.open(projectdir)

    latestbranch = project.branch(LATEST_BRANCH)
    updatebranch = project.heads.create(UPDATE_BRANCH, latestbranch.commit, force=True)

    with project.worktree(updatebranch, checkout=False) as worktree:
        template = createproject(worktree)
        Repository.open(worktree).commit(message=_commitmessage(template))

    project.cherrypick(updatebranch.commit)

    latestbranch.commit = updatebranch.commit


def _commitmessage(template: Template) -> str:
    if template.revision:
        return f"Update {template.name} to {template.revision}"
    else:
        return f"Update {template.name}"


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
