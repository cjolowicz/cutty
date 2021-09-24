"""Update a project with changes from its Cookiecutter template."""
from collections.abc import Callable
from collections.abc import Sequence
from pathlib import Path
from pathlib import PurePosixPath
from typing import Optional

import pygit2

from cutty.repositories.domain.repository import Repository as Template
from cutty.services.create import create
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

    def createproject(outputdir: Path) -> Template:
        _, template = create(
            projectconfig.template,
            outputdir=outputdir,
            outputdirisproject=True,
            extrabindings=extrabindings,
            no_input=no_input,
            checkout=checkout,
            directory=directory,
        )
        return template

    updateproject(projectdir, createproject)


CreateProject = Callable[[Path], Template]


def updateproject(projectdir: Path, createproject: CreateProject) -> None:
    """Update a project by applying changes between the generated trees."""
    project = Repository.open(projectdir)
    project.heads[UPDATE_BRANCH] = project.heads[LATEST_BRANCH]
    branch = project.branch(UPDATE_BRANCH)

    with project.worktree(branch, checkout=False) as worktree:
        template = createproject(worktree)

        try:
            repository = Repository.open(worktree)
        except pygit2.GitError:
            repository = Repository.init(worktree)

        if template.revision:
            message = f"Update {template.name} to {template.revision}"
        else:
            message = f"Update {template.name}"

        repository.commit(message=message)
        repository.heads.setdefault(LATEST_BRANCH, repository.head.commit)

    project.cherrypick(branch.commit)
    project.heads[LATEST_BRANCH] = branch.commit


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
