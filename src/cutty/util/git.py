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


class Heads(MutableMapping[str, pygit2.Commit]):
    """Heads in a git repository."""

    def __init__(self, repository: Repository) -> None:
        """Initialize."""
        self._repository = repository
        self._branches = repository._repository.branches

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

    def create(
        self, name: str, commit: Optional[pygit2.Commit] = None, *, force: bool = False
    ) -> Branch:
        """Create the branch with the given name and commit."""
        if commit is None:
            commit = self._repository.head.commit

        self._branches.create(name, commit, force=force)

        return Branch(self, name)


class Branch:
    """Branch in a git repository."""

    def __init__(self, branches: Heads, name: str) -> None:
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


class MergeConflictError(Exception):
    """The merge resulted in conflicts."""


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
    def heads(self) -> Heads:
        """Return the repository branches."""
        return Heads(self)

    def branch(self, name: str) -> Branch:
        """Return the branch with the given name."""
        heads = self.heads
        heads[name]
        return Branch(heads, name)

    @property
    def head(self) -> Branch:
        """Return the branch referenced by HEAD."""
        head = self._repository.references["HEAD"].target

        if isinstance(head, pygit2.Oid):
            raise ValueError("HEAD is detached")

        name = head.removeprefix("refs/heads/")
        return Branch(self.heads, name)

    def checkout(self, branch: Branch) -> None:
        """Check out the given branch."""
        reference = branch._branches._branches[branch.name]
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
        self,
        *,
        message: str = "",
        author: Optional[pygit2.Signature] = None,
        committer: Optional[pygit2.Signature] = None,
    ) -> None:
        """Commit all changes in the repository.

        If there are no changes relative to the parent, this is a noop.
        """
        repository = self._repository
        index = repository.index

        index.add_all()

        tree = index.write_tree()
        if not repository.head_is_unborn and tree == repository.head.peel().tree.id:
            return

        index.write()

        if author is None:
            author = self.default_signature

        if committer is None:
            committer = author

        parents = [] if repository.head_is_unborn else [repository.head.target]
        repository.create_commit("HEAD", author, committer, message, tree, parents)
        repository.state_cleanup()

    @contextmanager
    def worktree(self, branch: Branch, *, checkout: bool = True) -> Iterator[Path]:
        """Create a worktree for the branch in the repository."""
        with tempfile.TemporaryDirectory() as directory:
            name = hashlib.blake2b(branch.name.encode(), digest_size=32).hexdigest()
            path = Path(directory) / name
            worktree = self._repository.add_worktree(
                name, path, self._repository.branches[branch.name]
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

    def cherrypick(self, commit: pygit2.Commit) -> None:
        """Cherry-pick the commit onto the current branch."""
        self._repository.index.read()
        self._repository.cherrypick(commit.id)

        if self._repository.index.conflicts:
            paths = {
                side.path
                for _, ours, theirs in self._repository.index.conflicts
                for side in (ours, theirs)
                if side is not None
            }
            raise MergeConflictError(f"Merge conflicts: {', '.join(paths)}")

        self.commit(
            message=commit.message,
            author=commit.author,
            committer=self.default_signature,
        )

        self._repository.state_cleanup()

    @property
    def cherrypickhead(self) -> Optional[pygit2.Commit]:
        """Return the commit referenced by CHERRY_PICK_HEAD, or None."""
        reference = self._repository.references.get("CHERRY_PICK_HEAD")
        if reference is not None:
            return reference.peel(pygit2.Commit)
        return None

    def resetcherrypick(self) -> None:
        """Reset only files that were touched by a cherry-pick.

        Emulates `git reset --merge HEAD` by performing a hard reset on the
        files updated by CHERRY_PICK_HEAD, and resetting the index to HEAD.
        """
        self._repository.index.read_tree(self._repository.head.peel().tree)
        self._repository.index.write()

        commit = self.cherrypickhead
        if not commit:
            return

        [parent] = commit.parents

        diff = commit.tree.diff_to_tree(parent.tree)
        paths = [
            file.path
            for delta in diff.deltas
            for file in (delta.old_file, delta.new_file)
        ]

        self._repository.checkout(
            strategy=pygit2.GIT_CHECKOUT_FORCE | pygit2.GIT_CHECKOUT_REMOVE_UNTRACKED,
            paths=paths,
        )

        self._repository.state_cleanup()

    def createtag(self, name: str, *, message: str) -> None:
        """Create a tag at HEAD."""
        self._repository.create_tag(
            name,
            self._repository.head.target,
            pygit2.GIT_OBJ_COMMIT,
            self.default_signature,
            message,
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
