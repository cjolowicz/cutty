"""Update a project with changes from its Cookiecutter template."""
from collections.abc import Sequence
from pathlib import Path
from pathlib import PurePosixPath
from typing import Optional

from cutty.services.create import create
from cutty.services.git import creategitrepository
from cutty.services.git import LATEST_BRANCH
from cutty.services.git import UPDATE_BRANCH
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
    repository.heads[UPDATE_BRANCH] = repository.heads[LATEST_BRANCH]
    branch = repository.branch(UPDATE_BRANCH)

    with repository.worktree(branch, checkout=False) as worktree:
        project_dir, template = create(
            projectconfig.template,
            outputdir=worktree,
            outputdirisproject=True,
            extrabindings=extrabindings,
            no_input=no_input,
            checkout=checkout,
            directory=directory,
        )
        creategitrepository(project_dir, template.name, template.revision)

    repository.cherrypick(branch.commit)
    repository.heads[LATEST_BRANCH] = branch.commit


def continueupdate(*, projectdir: Optional[Path] = None) -> None:
    """Continue an update after conflict resolution."""
    if projectdir is None:
        projectdir = Path.cwd()

    repository = Repository.open(projectdir)

    if commit := repository.cherrypickhead:
        repository.commit(
            message=commit.message,
            author=commit.author,
            committer=repository.default_signature,
        )

    repository.heads[LATEST_BRANCH] = repository.heads[UPDATE_BRANCH]


def skipupdate(*, projectdir: Optional[Path] = None) -> None:
    """Skip an update with conflicts."""
    if projectdir is None:
        projectdir = Path.cwd()

    repository = Repository.open(projectdir)
    repository.resetcherrypick()

    repository.heads[LATEST_BRANCH] = repository.heads[UPDATE_BRANCH]


def abortupdate(*, projectdir: Optional[Path] = None) -> None:
    """Abort an update with conflicts."""
    if projectdir is None:
        projectdir = Path.cwd()

    repository = Repository.open(projectdir)
    repository.resetcherrypick()

    repository.heads[UPDATE_BRANCH] = repository.heads[LATEST_BRANCH]
