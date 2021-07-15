"""Update a project with changes from its Cookiecutter template."""
import contextlib
import json
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pygit2

from cutty.services.create import create


def getprojecttemplate(projectdir: Path) -> str:
    """Return the location of the project template."""
    text = (projectdir / ".cookiecutter.json").read_text()
    data = json.loads(text)
    result: str = data["_template"]
    return result


def getprojectcontext(projectdir: Path) -> dict[str, str]:
    """Return the Cookiecutter context of the project."""
    text = (projectdir / ".cookiecutter.json").read_text()
    data = json.loads(text)
    return {
        key: value
        for key, value in data.items()
        if isinstance(key, str) and isinstance(value, str)
    }


@contextlib.contextmanager
def createworktree(repositorypath: Path, branch: str) -> Iterator[Path]:
    """Create a worktree for the branch in the repository."""
    repository = pygit2.Repository(repositorypath)

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / branch
        worktree = repository.add_worktree(branch, path, repository.branches[branch])
        yield path

    # Prune with `force=True` because libgit2 thinks `worktree.path` still exists.
    worktree.prune(True)


def update() -> None:
    """Update a project with changes from its Cookiecutter template."""
    projectdir = Path.cwd()
    template = getprojecttemplate(projectdir)
    context = getprojectcontext(projectdir)
    create(
        template,
        no_input=True,
        outputdir=projectdir.parent,
        overwrite_if_exists=True,
        extra_context=context,
    )
