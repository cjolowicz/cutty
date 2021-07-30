"""Git utilities."""
from __future__ import annotations

import contextlib
import hashlib
import os
import tempfile
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pygit2

from cutty.compat.contextlib import contextmanager


@dataclass
class Repository:
    """Git repository."""

    repository: pygit2.Repository

    @classmethod
    def open(cls, path: Path) -> Repository:
        """Open an existing repository."""
        repository = pygit2.Repository(path)
        return cls(repository)

    @classmethod
    def discover(cls, path: Path) -> Optional[Repository]:
        """Discover an existing repository."""
        repositorypath = pygit2.discover_repository(path)
        if repositorypath is None:
            return None
        return cls.open(Path(repositorypath))

    @classmethod
    def init(cls, path: Path, *, head: Optional[str] = None) -> Repository:
        """Create a repository."""
        repository = pygit2.init_repository(path, initial_head=head)
        return cls(repository)

    @classmethod
    def clone(cls, url: str, destination: Path) -> None:
        """Clone a repository using a mirror configuration."""

        def _createremote(
            repository: pygit2.Repository, name: bytes, url: bytes
        ) -> pygit2.Remote:
            name_ = name.decode()
            repository.config[f"remote.{name_}.mirror"] = True
            return repository.remotes.create(name, url, "+refs/*:refs/*")

        repository = pygit2.clone_repository(
            url, str(destination), bare=True, remote=_createremote
        )

        _fix_repository_head(repository)


def _fix_repository_head(repository: pygit2.Repository) -> pygit2.Reference:
    """Work around a bug in libgit2 resulting in a bogus HEAD reference.

    Cloning with a remote callback results in HEAD pointing to the user's
    `init.defaultBranch` instead of the default branch of the cloned repository.
    """
    # https://github.com/libgit2/pygit2/issues/1073
    head = repository.references["HEAD"]

    with contextlib.suppress(KeyError):
        return head.resolve()

    for branch in ["main", "master"]:
        ref = f"refs/heads/{branch}"
        if ref in repository.references:
            head.set_target(ref, message="repair broken HEAD after clone")
            break

    return head.resolve()


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
    message: str = "",
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


def checkoutemptytree(repository: pygit2.Repository) -> None:
    """Check out an empty tree from the repository."""
    oid = repository.TreeBuilder().write()
    repository.checkout_tree(repository[oid])


@contextmanager
def createworktree(
    repository: pygit2.Repository,
    branch: str,
    *,
    checkout: bool = True,
) -> Iterator[Path]:
    """Create a worktree for the branch in the repository."""
    with tempfile.TemporaryDirectory() as directory:
        name = hashlib.blake2b(branch.encode(), digest_size=32).hexdigest()
        path = Path(directory) / name
        worktree = repository.add_worktree(name, path, repository.branches[branch])

        if not checkout:
            # Emulate `--no-checkout` by checking out an empty tree after the fact.
            # https://github.com/libgit2/libgit2/issues/5949
            worktreerepository = Repository.open(path).repository
            checkoutemptytree(worktreerepository)

        yield path

    # Prune with `force=True` because libgit2 thinks `worktree.path` still exists.
    # https://github.com/libgit2/libgit2/issues/5280
    worktree.prune(True)


def cherrypick(repository: pygit2.Repository, reference: str, *, message: str) -> None:
    """Cherry-pick the commit onto the current branch."""
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
    repository: pygit2.Repository,
    branch: str,
    *,
    target: str = "HEAD",
    force: bool = False,
) -> pygit2.Branch:
    """Create a branch pointing to the given target."""
    commit = repository.revparse_single(target)
    return repository.branches.create(branch, commit, force=force)


def updatebranch(repository: pygit2.Repository, branch: str, *, target: str) -> None:
    """Update a branch to the given target, another branch."""
    commit = repository.branches[target].peel()
    repository.branches[branch].set_target(commit.id)


def resetmerge(repository: pygit2.Repository, parent: str, cherry: str) -> None:
    """Reset only files that were touched by a cherry-pick.

    This emulates `git reset --merge HEAD` by performing a hard reset on the
    files that were updated by the cherry-picked commit, and resetting the index
    to HEAD.
    """
    repository.index.read_tree(repository.head.peel().tree)
    repository.index.write()

    parenttree = repository.branches[parent].peel(pygit2.Tree)
    cherrytree = repository.branches[cherry].peel(pygit2.Tree)
    diff = cherrytree.diff_to_tree(parenttree)
    paths = [
        file.path for delta in diff.deltas for file in (delta.old_file, delta.new_file)
    ]

    repository.checkout(
        strategy=pygit2.GIT_CHECKOUT_FORCE | pygit2.GIT_CHECKOUT_REMOVE_UNTRACKED,
        paths=paths,
    )