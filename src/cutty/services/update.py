"""Update a project with changes from its Cookiecutter template."""
import hashlib
import tempfile
from collections.abc import Iterator
from pathlib import Path
from pathlib import PurePosixPath
from typing import Optional
from typing import Sequence

import pygit2

from cutty.compat.contextlib import contextmanager
from cutty.filestorage.adapters.observers.git import commit
from cutty.filestorage.adapters.observers.git import LATEST_BRANCH
from cutty.filestorage.adapters.observers.git import UPDATE_BRANCH
from cutty.filestorage.adapters.observers.git import UPDATE_BRANCH_REF
from cutty.filestorage.adapters.observers.git import UPDATE_MESSAGE
from cutty.services.create import create
from cutty.templates.adapters.cookiecutter.projectconfig import readprojectconfigfile
from cutty.templates.domain.bindings import Binding


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
            # https://github.com/libgit2/libgit2/issues/5949
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


def createbranch(
    repositorypath: Path, branch: str, *, target: str, force: bool = False
) -> None:
    """Create a branch pointing to the given target, another branch."""
    repository = pygit2.Repository(repositorypath)
    commit = repository.branches[target].peel()
    repository.branches.create(branch, commit, force=force)


def updatebranch(repositorypath: Path, branch: str, *, target: str) -> None:
    """Update a branch to the given target, another branch."""
    repository = pygit2.Repository(repositorypath)
    commit = repository.branches[target].peel()
    repository.branches[branch].set_target(commit.id)


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

    createbranch(projectdir, UPDATE_BRANCH, target=LATEST_BRANCH, force=True)

    with createworktree(projectdir, UPDATE_BRANCH, checkout=False) as worktree:
        create(
            projectconfig.template,
            outputdir=worktree,
            outputdirisproject=True,
            extrabindings=extrabindings,
            no_input=no_input,
            checkout=checkout,
            directory=directory,
        )

    cherrypick(projectdir, UPDATE_BRANCH_REF)

    updatebranch(projectdir, LATEST_BRANCH, target=UPDATE_BRANCH)


def continueupdate(*, projectdir: Optional[Path] = None) -> None:
    """Continue an update after conflict resolution."""
    if projectdir is None:
        projectdir = Path.cwd()

    commit(pygit2.Repository(projectdir), message=UPDATE_MESSAGE)
    updatebranch(projectdir, LATEST_BRANCH, target=UPDATE_BRANCH)


def skipupdate(*, projectdir: Optional[Path] = None) -> None:
    """Skip an update with conflicts."""
    if projectdir is None:
        projectdir = Path.cwd()

    repository = pygit2.Repository(projectdir)
    repository.index.read_tree(repository.head.peel().tree)
    repository.index.write()
    repository.checkout(strategy=pygit2.GIT_CHECKOUT_FORCE)

    updatebranch(projectdir, LATEST_BRANCH, target=UPDATE_BRANCH)
