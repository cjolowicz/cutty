"""Update a project with changes from its Cookiecutter template."""
import hashlib
import json
import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import Optional

import pygit2

from cutty.compat.contextlib import contextmanager
from cutty.filestorage.adapters.observers.git import commit
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
    repositorypath: Path,
    branch: str,
    *,
    dirname: Optional[str] = None,
    checkout: bool = True,
) -> Iterator[Path]:
    """Create a worktree for the branch in the repository."""
    if dirname is None:
        dirname = branch

    repository = pygit2.Repository(repositorypath)

    with tempfile.TemporaryDirectory() as directory:
        name = hashlib.blake2b(branch.encode(), digest_size=32).hexdigest()
        path = Path(directory) / dirname
        worktree = repository.add_worktree(name, path, repository.branches[branch])

        if not checkout:
            # Emulate `--no-checkout` by checking out an empty tree after the fact.
            worktree_repository = pygit2.Repository(path)
            oid = worktree_repository.TreeBuilder().write()
            worktree_repository.checkout_tree(worktree_repository[oid])

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
            path
            for _, ours, theirs in repository.index.conflicts
            for path in (ours.path, theirs.path)
        }
        raise RuntimeError(f"Merge conflicts: {' '.join(paths)}")

    commit(repository, message="Update project template")
    repository.state_cleanup()


def update() -> None:
    """Update a project with changes from its Cookiecutter template."""
    projectdir = Path.cwd()
    template = getprojecttemplate(projectdir)
    context = getprojectcontext(projectdir)
    with createworktree(
        projectdir, "cutty/latest", dirname=projectdir.name, checkout=False
    ) as worktree:
        create(
            template,
            no_input=True,
            outputdir=worktree.parent,
            overwrite_if_exists=True,
            extra_context=context,
        )
    cherrypick(projectdir, "refs/heads/cutty/latest")
