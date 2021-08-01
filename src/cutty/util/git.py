"""Git utilities."""
from __future__ import annotations

import contextlib
import hashlib
import os
import tempfile
from collections.abc import Iterator
from collections.abc import MutableMapping
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pygit2.repository

from cutty.compat.contextlib import contextmanager


class Branches(MutableMapping[str, pygit2.Commit]):
    """Branches in a git repository."""

    def __init__(self, branches: pygit2.repository.Branches) -> None:
        """Initialize."""
        self._branches = branches

    def __len__(self) -> int:
        """Return the number of branches."""
        return sum(1 for _ in self._branches)

    def __bool__(self) -> bool:
        """Return True if there are any branches."""
        for _ in self._branches:
            return True
        return False

    def __iter__(self) -> Iterator[str]:
        """Iterate over the branches."""
        return iter(self._branches)

    def __getitem__(self, name: str) -> pygit2.Commit:
        """Return the commit at the head of the branch."""
        return self._branches[name].peel(pygit2.Commit)

    def __setitem__(self, name: str, commit: pygit2.Commit) -> None:
        """Create the branch, or reset the branch to another commit."""
        self._branches.create(name, commit, force=True)

    def __delitem__(self, name: str) -> None:
        """Remove the branch."""
        self._branches.delete(name)

    def branch(self, name: str) -> Branch:
        """Return the branch with the given name."""
        self[name]
        return Branch(self, name)

    def create(self, name: str, commit: pygit2.Commit) -> Branch:
        """Create the branch with the given name and commit."""
        self._branches.create(name, commit)
        return Branch(self, name)


class Branch:
    """Branch in a git repository."""

    def __init__(self, branches: Branches, name: str) -> None:
        """Initialize."""
        self._branches = branches
        self._name = name

    @property
    def name(self) -> str:
        """Return the name of the branch."""
        return self._name

    @property
    def commit(self) -> pygit2.Commit:
        """Return the commit at the head of branch."""
        return self._branches[self._name]

    @commit.setter
    def commit(self, commit: pygit2.Commit) -> None:
        """Reset the branch to another commit."""
        self._branches[self._name] = commit


@dataclass
class Repository:
    """Git repository."""

    _repository: pygit2.Repository
    path: Path

    @classmethod
    def open(cls, path: Path) -> Repository:
        """Open an existing repository."""
        repository = pygit2.Repository(path)
        return cls(repository, path)

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
        return cls(repository, path)

    @classmethod
    def clone(cls, url: str, destination: Path, *, mirror: bool = False) -> None:
        """Clone a repository using a mirror configuration."""
        if not mirror:  # pragma: no cover
            raise NotImplementedError("clone without mirror is not implemented")

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

    def fetch(self, *, prune: bool = False) -> None:
        """Fetch all remotes."""
        if not prune:  # pragma: no cover
            raise NotImplementedError("fetch without prune is not implemented")

        for remote in self._repository.remotes:
            remote.fetch(prune=pygit2.GIT_FETCH_PRUNE)

    @property
    def index(self) -> pygit2.Index:
        """Return the repository index."""
        return self._repository.index

    @property
    def head(self) -> pygit2.Reference:
        """Return the repository head."""
        return self._repository.head

    def set_head(self, target: str) -> None:
        """Update the repository head."""
        self._repository.set_head(target)

    @property
    def references(self) -> pygit2.repository.References:
        """Return the repository references."""
        return self._repository.references

    @property
    def branches(self) -> Branches:
        """Return the repository branches."""
        return Branches(self._repository.branches)

    def checkout(self, reference: pygit2.Reference) -> None:
        """Check out the given reference."""
        self._repository.checkout(reference)

    @property
    def default_signature(self) -> pygit2.Signature:
        """Return the default signature."""
        with contextlib.suppress(KeyError):
            return pygit2.Signature(
                os.environ["GIT_AUTHOR_NAME"],
                os.environ["GIT_AUTHOR_EMAIL"],
            )
        return self._repository.default_signature  # pragma: no cover

    def commit(
        self, *, message: str = "", signature: Optional[pygit2.Signature] = None
    ) -> None:
        """Commit all changes in the repository.

        If there are no changes relative to the parent, this is a noop.
        """
        self.index.add_all()

        tree = self.index.write_tree()
        if not self._repository.head_is_unborn and tree == self.head.peel().tree.id:
            return

        self.index.write()

        if signature is None:
            signature = self.default_signature

        parents = [] if self._repository.head_is_unborn else [self.head.target]
        self._repository.create_commit(
            "HEAD", signature, signature, message, tree, parents
        )

    @contextmanager
    def createworktree(self, branch: str, *, checkout: bool = True) -> Iterator[Path]:
        """Create a worktree for the branch in the repository."""
        with tempfile.TemporaryDirectory() as directory:
            name = hashlib.blake2b(branch.encode(), digest_size=32).hexdigest()
            path = Path(directory) / name
            worktree = self._repository.add_worktree(
                name, path, self._repository.branches[branch]
            )

            if not checkout:
                # Emulate `--no-checkout` by checking out an empty tree after the fact.
                # https://github.com/libgit2/libgit2/issues/5949
                Repository.open(path)._checkoutemptytree()

            yield path

        # Prune with `force=True` because libgit2 thinks `worktree.path` still exists.
        # https://github.com/libgit2/libgit2/issues/5280
        worktree.prune(True)

    def _checkoutemptytree(self) -> None:
        """Check out an empty tree from the repository."""
        oid = self._repository.TreeBuilder().write()
        self._repository.checkout_tree(self._repository[oid])

    def cherrypick(self, reference: str, *, message: str) -> None:
        """Cherry-pick the commit onto the current branch."""
        oid = self._repository.references[reference].resolve().target
        self._repository.cherrypick(oid)

        if self._repository.index.conflicts:
            paths = {
                side.path
                for _, ours, theirs in self._repository.index.conflicts
                for side in (ours, theirs)
                if side is not None
            }
            raise RuntimeError(f"Merge conflicts: {', '.join(paths)}")

        self.commit(message=message)
        self._repository.state_cleanup()

    def createtag(self, name: str, *, message: str) -> None:
        """Create a tag at HEAD."""
        self._repository.create_tag(
            name,
            self.head.target,
            pygit2.GIT_OBJ_COMMIT,
            self.default_signature,
            message,
        )

    def createbranch(
        self, branch: str, *, target: str = "HEAD", force: bool = False
    ) -> pygit2.Branch:
        """Create a branch pointing to the given target."""
        commit = self._repository.revparse_single(target)
        return self._repository.branches.create(branch, commit, force=force)

    def updatebranch(self, branch: str, *, target: str) -> None:
        """Update a branch to the given target, another branch."""
        self.branches[branch] = self.branches[target]

    def resetmerge(self, parent: str, cherry: str) -> None:
        """Reset only files that were touched by a cherry-pick.

        This emulates `git reset --merge HEAD` by performing a hard reset on the
        files that were updated by the cherry-picked commit, and resetting the index
        to HEAD.
        """
        self._repository.index.read_tree(self._repository.head.peel().tree)
        self._repository.index.write()

        parenttree = self.branches[parent].peel(pygit2.Tree)
        cherrytree = self.branches[cherry].peel(pygit2.Tree)
        diff = cherrytree.diff_to_tree(parenttree)
        paths = [
            file.path
            for delta in diff.deltas
            for file in (delta.old_file, delta.new_file)
        ]

        self._repository.checkout(
            strategy=pygit2.GIT_CHECKOUT_FORCE | pygit2.GIT_CHECKOUT_REMOVE_UNTRACKED,
            paths=paths,
        )


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
