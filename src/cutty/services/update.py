"""Update a project with changes from its Cookiecutter template."""
import hashlib
import json
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pygit2

from cutty.compat.contextlib import contextmanager
from cutty.filestorage.adapters.observers.git import commit
from cutty.filestorage.adapters.observers.git import LATEST_BRANCH
from cutty.filestorage.adapters.observers.git import UPDATE_MESSAGE
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


def checkoutemptytree(repositorypath: Path) -> None:
    """Check out an empty tree from the repository."""
    repository = pygit2.Repository(repositorypath)
    oid = repository.TreeBuilder().write()
    repository.checkout_tree(repository[oid])


@contextmanager
def createworktree(
    repositorypath: Path,
    branch: str,
    *,
    checkout: bool = True,
) -> Iterator[Path]:
    """Create a worktree for the branch in the repository."""
    repository = pygit2.Repository(repositorypath)

    with tempfile.TemporaryDirectory() as directory:
        name = hashlib.blake2b(branch.encode(), digest_size=32).hexdigest()
        path = Path(directory) / name
        worktree = repository.add_worktree(name, path, repository.branches[branch])

        if not checkout:
            # Emulate `--no-checkout` by checking out an empty tree after the fact.
            checkoutemptytree(path)

        yield path

    # Prune with `force=True` because libgit2 thinks `worktree.path` still exists.
    # https://github.com/libgit2/libgit2/issues/5280
    worktree.prune(True)


def cherrypick(repositorypath: Path, reference: str) -> None:
    """Cherry-pick the commit onto the current branch."""
    repository = pygit2.Repository(repositorypath)
    oid = repository.references[reference].resolve().target
    repository.cherrypick(oid)

    if repository.index.conflicts:
        paths = {
            side.path
            for _, ours, theirs in repository.index.conflicts
            for side in (ours, theirs)
            if side is not None
        }
        raise RuntimeError(f"Merge conflicts: {', '.join(paths)}")

    commit(repository, message=UPDATE_MESSAGE)
    repository.state_cleanup()


def update() -> None:
    """Update a project with changes from its Cookiecutter template."""
    projectdir = Path.cwd()
    template = getprojecttemplate(projectdir)
    context = getprojectcontext(projectdir)

    with createworktree(projectdir, LATEST_BRANCH, checkout=False) as worktree:
        create(
            template,
            outputdir=worktree,
            outputdirisproject=True,
            extra_context=context,
        )

    cherrypick(projectdir, f"refs/heads/{LATEST_BRANCH}")
