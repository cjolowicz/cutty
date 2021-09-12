"""Link a project to a Cookiecutter template."""
import pathlib
from collections.abc import Sequence
from typing import Optional

from cutty.filestorage.adapters.observers.git import LATEST_BRANCH
from cutty.filestorage.adapters.observers.git import UPDATE_BRANCH
from cutty.services.create import create
from cutty.templates.domain.bindings import Binding
from cutty.util.git import Repository


def link(
    template: str,
    *,
    extrabindings: Sequence[Binding] = (),
    no_input: bool = False,
    projectdir: Optional[pathlib.Path] = None
) -> None:
    """Link project to a Cookiecutter template."""
    if projectdir is None:
        projectdir = pathlib.Path.cwd()

    project = Repository.open(projectdir)
    branch = project.heads.create(UPDATE_BRANCH)  # XXX orphan branch would be better

    with project.worktree(branch, checkout=False) as worktree:
        create(
            template,
            outputdir=worktree,
            outputdirisproject=True,
            extrabindings=extrabindings,
            no_input=no_input,
            checkout=None,
            directory=None,
        )

    (project.path / "cutty.json").write_bytes((branch.commit.tree / "cutty.json").data)
    project.commit(message="Link to project template")  # XXX mention name and revision

    project.heads[LATEST_BRANCH] = branch.commit
