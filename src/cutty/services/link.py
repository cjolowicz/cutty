"""Link a project to a Cookiecutter template."""
import pathlib

from cutty.filestorage.adapters.observers.git import LATEST_BRANCH
from cutty.filestorage.adapters.observers.git import UPDATE_BRANCH
from cutty.services.create import create
from cutty.util.git import Repository


def link(template: str) -> None:
    """Link project to a Cookiecutter template."""
    project = Repository.open(pathlib.Path.cwd())
    branch = project.heads.create(UPDATE_BRANCH)  # XXX orphan branch would be better

    with project.worktree(branch, checkout=False) as worktree:
        create(
            template,
            outputdir=worktree,
            outputdirisproject=True,
            extrabindings=(),
            no_input=False,
            checkout=None,
            directory=None,
        )

    (project.path / "cutty.json").write_bytes((branch.commit.tree / "cutty.json").data)
    project.commit(message="Link to project template")  # XXX mention name and revision

    project.heads[LATEST_BRANCH] = branch.commit
