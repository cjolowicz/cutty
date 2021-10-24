"""Project repositories."""
from __future__ import annotations

from collections.abc import Iterable
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pygit2

from cutty.compat.contextlib import contextmanager
from cutty.errors import CuttyError
from cutty.util.git import Repository


UPDATE_BRANCH = "cutty/update"


class NoUpdateInProgressError(CuttyError):
    """A sequencer action was invoked without an update in progress."""


@dataclass
class ProjectBuilder:
    """Adding a project to the repository."""

    _worktree: Repository

    @property
    def path(self) -> Path:
        """Return the project directory."""
        return self._worktree.path

    def commit(self, message: str) -> str:
        """Commit the project."""
        self._worktree.commit(message=message)
        return str(self._worktree.head.commit.id)


class ProjectRepository:
    """Project repository."""

    def __init__(self, path: Path) -> None:
        """Initialize."""
        self.project = Repository.open(path)

    @classmethod
    def create(cls, projectdir: Path, message: str = "") -> ProjectRepository:
        """Initialize the git repository for a project."""
        try:
            repository = cls(projectdir)
        except pygit2.GitError:
            Repository.init(projectdir)
            repository = cls(projectdir)

        if repository.project._repository.head_is_unborn:
            repository._createroot(message=message)

        return repository

    def _createroot(
        self, *, updateref: Optional[str] = "HEAD", message: str = ""
    ) -> str:
        """Create an empty root commit."""
        author = committer = self.project.default_signature
        repository = self.project._repository
        tree = repository.TreeBuilder().write()
        oid = repository.create_commit(updateref, author, committer, message, tree, [])
        return str(oid)

    @contextmanager
    def build(self, *, parent: Optional[str] = None) -> Iterator[ProjectBuilder]:
        """Create a commit with a generated project."""
        if parent is None:
            parent = self._createroot(updateref=None)

        branch = self.project.heads.create(
            UPDATE_BRANCH, self.project._repository[parent], force=True
        )

        try:
            with self.project.worktree(branch, checkout=False) as worktree:
                builder = ProjectBuilder(worktree)
                yield builder
        finally:
            self.project.heads.pop(branch.name)

    def import_(self, commit: str, *, paths: Iterable[Path] = ()) -> None:
        """Import changes to the project made by the given commit."""
        cherry = self.project._repository[commit]

        if not paths:
            self.project.cherrypick(cherry)
            return

        for path in paths:
            (self.project.path / path).write_bytes((cherry.tree / path).data)
            self.project._repository.index.add(path)

        self.project.commit(
            message=cherry.message,
            author=cherry.author,
            committer=self.project.default_signature,
            stageallfiles=False,
        )

    def continue_(self) -> None:
        """Continue an update after conflict resolution."""
        if not (commit := self.project.cherrypickhead):
            raise NoUpdateInProgressError()

        self.project.commit(
            message=commit.message,
            author=commit.author,
            committer=self.project.default_signature,
        )

    def abort(self) -> None:
        """Abort an update with conflicts."""
        if not self.project.cherrypickhead:
            raise NoUpdateInProgressError()

        self.project.resetcherrypick()
