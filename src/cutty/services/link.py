"""Link a project to a Cookiecutter template."""
import pathlib
from collections.abc import Sequence
from typing import Optional

from cutty.filestorage.adapters.observers.git import LATEST_BRANCH
from cutty.filestorage.adapters.observers.git import UPDATE_BRANCH
from cutty.services.create import create
from cutty.templates.adapters.cookiecutter.projectconfig import PROJECT_CONFIG_FILE
from cutty.templates.domain.bindings import Binding
from cutty.util.git import Repository


def link(
    template: str,
    *,
    extrabindings: Sequence[Binding] = (),
    no_input: bool = False,
    checkout: Optional[str] = None,
    directory: Optional[pathlib.PurePosixPath] = None,
    projectdir: Optional[pathlib.Path] = None
) -> None:
    """Link project to a Cookiecutter template."""
    if projectdir is None:
        projectdir = pathlib.Path.cwd()

    project = Repository.open(projectdir)
    latest = project.heads.setdefault(LATEST_BRANCH, project.head.commit)
    branch = project.heads.create(UPDATE_BRANCH, latest, force=True)
    # XXX orphan branch would be better

    with project.worktree(branch, checkout=False) as worktree:
        create(
            template,
            outputdir=worktree,
            outputdirisproject=True,
            extrabindings=extrabindings,
            no_input=no_input,
            checkout=checkout,
            directory=directory,
        )

    (project.path / PROJECT_CONFIG_FILE).write_bytes(
        (branch.commit.tree / PROJECT_CONFIG_FILE).data
    )
    project.commit(message="Link to project template")  # XXX mention name and revision

    project.heads[LATEST_BRANCH] = branch.commit
