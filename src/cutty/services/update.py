"""Update a project with changes from its Cookiecutter template."""
from collections.abc import Sequence
from pathlib import Path
from pathlib import PurePosixPath
from typing import Optional

import pygit2

from cutty.filestorage.adapters.observers.git import LATEST_BRANCH
from cutty.filestorage.adapters.observers.git import UPDATE_BRANCH
from cutty.filestorage.adapters.observers.git import UPDATE_BRANCH_REF
from cutty.filestorage.adapters.observers.git import UPDATE_MESSAGE
from cutty.services.create import create
from cutty.templates.adapters.cookiecutter.projectconfig import readprojectconfigfile
from cutty.templates.domain.bindings import Binding
from cutty.util.git import cherrypick
from cutty.util.git import commit
from cutty.util.git import createbranch
from cutty.util.git import createworktree
from cutty.util.git import updatebranch


def update(
    *,
    projectdir: Optional[Path] = None,
    extrabindings: Sequence[Binding] = (),
    no_input: bool = False,
    checkout: Optional[str] = None,
    directory: Optional[PurePosixPath] = None,
) -> None:
    """Update a project with changes from its Cookiecutter template."""
    if projectdir is None:
        projectdir = Path.cwd()

    projectconfig = readprojectconfigfile(projectdir)
    extrabindings = list(projectconfig.bindings) + list(extrabindings)

    if directory is None:
        directory = projectconfig.directory

    createbranch(projectdir, UPDATE_BRANCH, target=LATEST_BRANCH, force=True)

    with createworktree(projectdir, UPDATE_BRANCH, checkout=False) as worktree:
        create(
            projectconfig.template,
            outputdir=worktree,
            outputdirisproject=True,
            extrabindings=extrabindings,
            no_input=no_input,
            checkout=checkout,
            directory=directory,
        )

    cherrypick(projectdir, UPDATE_BRANCH_REF, message=UPDATE_MESSAGE)

    updatebranch(projectdir, LATEST_BRANCH, target=UPDATE_BRANCH)


def continueupdate(*, projectdir: Optional[Path] = None) -> None:
    """Continue an update after conflict resolution."""
    if projectdir is None:
        projectdir = Path.cwd()

    commit(pygit2.Repository(projectdir), message=UPDATE_MESSAGE)
    updatebranch(projectdir, LATEST_BRANCH, target=UPDATE_BRANCH)


def resetmerge(repositorypath: Path, parent: str, cherry: str) -> None:
    """Reset only files that were touched by a cherry-pick.

    This emulates `git reset --merge HEAD` by performing a hard reset on the
    files that were updated by the cherry-picked commit, and resetting the index
    to HEAD.
    """
    from cutty.util.git import resetmerge

    resetmerge(repositorypath, parent, cherry)


def skipupdate(*, projectdir: Optional[Path] = None) -> None:
    """Skip an update with conflicts."""
    if projectdir is None:
        projectdir = Path.cwd()

    resetmerge(projectdir, parent=LATEST_BRANCH, cherry=UPDATE_BRANCH)
    updatebranch(projectdir, LATEST_BRANCH, target=UPDATE_BRANCH)


def abortupdate(*, projectdir: Optional[Path] = None) -> None:
    """Abort an update with conflicts."""
    if projectdir is None:
        projectdir = Path.cwd()

    resetmerge(projectdir, parent=LATEST_BRANCH, cherry=UPDATE_BRANCH)
    updatebranch(projectdir, UPDATE_BRANCH, target=LATEST_BRANCH)
