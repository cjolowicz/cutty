"""Update a project with changes from its Cookiecutter template."""
import hashlib
import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import Optional
from typing import Sequence

import pygit2

from cutty.compat.contextlib import contextmanager
from cutty.filestorage.adapters.observers.git import commit
from cutty.filestorage.adapters.observers.git import LATEST_BRANCH
from cutty.filestorage.adapters.observers.git import UPDATE_MESSAGE
from cutty.services.create import create
from cutty.templates.adapters.cookiecutter.projectconfig import getprojecttemplate
from cutty.templates.adapters.cookiecutter.projectconfig import readprojectconfigfile
from cutty.templates.domain.bindings import Binding


def getprojectbindings(projectdir: Path) -> Sequence[Binding]:
    """Return the variable bindings of the project."""
    context = readprojectconfigfile(projectdir)
    return [Binding(key, value) for key, value in context.items()]


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


def update(
    *,
    projectdir: Optional[Path] = None,
    extrabindings: Sequence[Binding] = (),
    no_input: bool = False,
) -> None:
    """Update a project with changes from its Cookiecutter template."""
    if projectdir is None:
        projectdir = Path.cwd()

    template = getprojecttemplate(projectdir)
    bindings = getprojectbindings(projectdir)
    extrabindings = list(bindings) + list(extrabindings)

    with createworktree(projectdir, LATEST_BRANCH, checkout=False) as worktree:
        create(
            template,
            outputdir=worktree,
            outputdirisproject=True,
            extrabindings=extrabindings,
            no_input=no_input,
        )

    cherrypick(projectdir, f"refs/heads/{LATEST_BRANCH}")
