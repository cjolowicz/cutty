"""Update a project with changes from its Cookiecutter template."""
from collections.abc import Sequence
from pathlib import Path
from pathlib import PurePosixPath
from typing import Optional

from cutty.projects.create import LATEST_BRANCH
from cutty.projects.create import UPDATE_BRANCH
from cutty.projects.update import updateproject
from cutty.repositories.domain.repository import Repository as Template
from cutty.services.create import create
from cutty.templates.adapters.cookiecutter.projectconfig import readprojectconfigfile
from cutty.templates.domain.bindings import Binding
from cutty.util.git import Repository


def update(
    projectdir: Path,
    *,
    extrabindings: Sequence[Binding] = (),
    no_input: bool = False,
    checkout: Optional[str] = None,
    directory: Optional[PurePosixPath] = None,
) -> None:
    """Update a project with changes from its Cookiecutter template."""
    projectconfig = readprojectconfigfile(projectdir)
    extrabindings = list(projectconfig.bindings) + list(extrabindings)

    if directory is None:
        directory = projectconfig.directory

    def createproject(outputdir: Path) -> Template:
        _, template = create(
            projectconfig.template,
            outputdir,
            outputdirisproject=True,
            extrabindings=extrabindings,
            no_input=no_input,
            checkout=checkout,
            directory=directory,
        )
        return template

    updateproject(projectdir, createproject)


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
