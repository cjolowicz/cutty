"""Update a project with changes from its Cookiecutter template."""
import json
import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import Optional

import pygit2

from cutty.compat.contextlib import contextmanager
from cutty.services.create import create


def getprojecttemplate(projectdir: Path) -> str:
    """Return the location of the project template."""
    context = getprojectcontext(projectdir)
    return context["_template"]


def getprojectcontext(projectdir: Path) -> dict[str, str]:
    """Return the Cookiecutter context of the project."""
    text = (projectdir / ".cookiecutter.json").read_text()
    data = json.loads(text)
    return {
        key: value
        for key, value in data.items()
        if isinstance(key, str) and isinstance(value, str)
    }


@contextmanager
def createworktree(
    repositorypath: Path, branch: str, dirname: Optional[str] = None
) -> Iterator[Path]:
    """Create a worktree for the branch in the repository."""
    if dirname is None:
        dirname = branch

    repository = pygit2.Repository(repositorypath)

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / dirname
        worktree = repository.add_worktree(branch, path, repository.branches[branch])
        yield path

    # Prune with `force=True` because libgit2 thinks `worktree.path` still exists.
    # https://github.com/libgit2/libgit2/issues/5280
    worktree.prune(True)


def update() -> None:
    """Update a project with changes from its Cookiecutter template."""
    projectdir = Path.cwd()
    template = getprojecttemplate(projectdir)
    context = getprojectcontext(projectdir)
    with createworktree(
        projectdir, "cutty/latest", dirname=projectdir.name
    ) as worktree:
        create(
            template,
            no_input=True,
            outputdir=worktree.parent,
            overwrite_if_exists=True,
            extra_context=context,
        )
