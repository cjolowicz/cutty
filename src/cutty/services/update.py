"""Update a project with changes from its Cookiecutter template."""
from collections.abc import Sequence
from pathlib import Path
from pathlib import PurePosixPath
from typing import Optional

from cutty.filestorage.adapters.observers.git import LATEST_BRANCH
from cutty.filestorage.adapters.observers.git import UPDATE_BRANCH
from cutty.filestorage.adapters.observers.git import UPDATE_BRANCH_REF
from cutty.filestorage.adapters.observers.git import UPDATE_MESSAGE
from cutty.services.create import create
from cutty.templates.adapters.cookiecutter.projectconfig import readprojectconfigfile
from cutty.templates.domain.bindings import Binding
from cutty.util.git import Repository


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

    repository = Repository.open(projectdir)
    repository.branches[UPDATE_BRANCH] = repository.branches[LATEST_BRANCH]

    with repository.createworktree(UPDATE_BRANCH, checkout=False) as worktree:
        create(
            projectconfig.template,
            outputdir=worktree,
            outputdirisproject=True,
            extrabindings=extrabindings,
            no_input=no_input,
            checkout=checkout,
            directory=directory,
        )

    repository.cherrypick(UPDATE_BRANCH_REF, message=UPDATE_MESSAGE)
    repository.branches[LATEST_BRANCH] = repository.branches[UPDATE_BRANCH]


def continueupdate(*, projectdir: Optional[Path] = None) -> None:
    """Continue an update after conflict resolution."""
    if projectdir is None:
        projectdir = Path.cwd()

    repository = Repository.open(projectdir)
    repository.commit(message=UPDATE_MESSAGE)
    repository.branches[LATEST_BRANCH] = repository.branches[UPDATE_BRANCH]


def skipupdate(*, projectdir: Optional[Path] = None) -> None:
    """Skip an update with conflicts."""
    if projectdir is None:
        projectdir = Path.cwd()

    repository = Repository.open(projectdir)
    repository.resetmerge(parent=LATEST_BRANCH, cherry=UPDATE_BRANCH)
    repository.branches[LATEST_BRANCH] = repository.branches[UPDATE_BRANCH]


def abortupdate(*, projectdir: Optional[Path] = None) -> None:
    """Abort an update with conflicts."""
    if projectdir is None:
        projectdir = Path.cwd()

    repository = Repository.open(projectdir)
    repository.resetmerge(parent=LATEST_BRANCH, cherry=UPDATE_BRANCH)
    repository.branches[UPDATE_BRANCH] = repository.branches[LATEST_BRANCH]
