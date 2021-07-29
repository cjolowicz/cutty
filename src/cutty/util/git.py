"""Git utilities."""
import contextlib
import hashlib
import os
import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import Optional

import pygit2

from cutty.compat.contextlib import contextmanager


def default_signature(repository: pygit2.Repository) -> pygit2.Signature:
    """Return the default signature."""
    with contextlib.suppress(KeyError):
        return pygit2.Signature(
            os.environ["GIT_AUTHOR_NAME"],
            os.environ["GIT_AUTHOR_EMAIL"],
        )
    return repository.default_signature  # pragma: no cover


def commit(
    repository: pygit2.Repository,
    *,
    message: str,
    signature: Optional[pygit2.Signature] = None,
) -> None:
    """Commit all changes in the repository.

    If there are no changes relative to the parent, this is a noop.
    """
    repository.index.add_all()

    tree = repository.index.write_tree()
    if not repository.head_is_unborn and tree == repository.head.peel().tree.id:
        return

    repository.index.write()

    if signature is None:
        signature = default_signature(repository)

    parents = [] if repository.head_is_unborn else [repository.head.target]
    repository.create_commit("HEAD", signature, signature, message, tree, parents)


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


def cherrypick(repositorypath: Path, reference: str, *, message: str) -> None:
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

    commit(repository, message=message)
    repository.state_cleanup()


def createbranch(
    repositorypath: Path, branch: str, *, target: str, force: bool = False
) -> None:
    """Create a branch pointing to the given target, another branch."""
    repository = pygit2.Repository(repositorypath)
    commit = repository.branches[target].peel()
    repository.branches.create(branch, commit, force=force)
