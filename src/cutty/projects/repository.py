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
    def create(cls, projectdir: Path) -> ProjectRepository:
        """Initialize the git repository for a project."""
        try:
            repository = cls(projectdir)
        except pygit2.GitError:
            Repository.init(projectdir)
            repository = cls(projectdir)

        if repository.project._repository.head_is_unborn:
            repository._createroot()

        return repository

    def _createroot(self, *, updateref: Optional[str] = "HEAD") -> str:
        """Create an empty root commit."""
        author = committer = self.project.default_signature
        repository = self.project._repository
        tree = repository.TreeBuilder().write()
        oid = repository.create_commit(updateref, author, committer, "", tree, [])
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

    def link(self, commit: str, *files: Path, message: str) -> None:
        """Update the project configuration."""
        self.import2(commit, message=message, files=files)

    def import2(self, commit: str, *, message: str, files: Iterable[Path]) -> None:
        """Import changes to the project made by the given commit."""
        commit2 = self.project._repository[commit]

        for filename in files:
            (self.project.path / filename).write_bytes((commit2.tree / filename).data)
            self.project._repository.index.add(filename)

        self.project.commit(
            message=message,
            author=commit2.author,
            committer=self.project.default_signature,
            stageallfiles=False,
        )

    def import_(self, commit: str) -> None:
        """Import changes to the project made by the given commit."""
        self.project.cherrypick(self.project._repository[commit])

    def continueupdate(self) -> None:
        """Continue an update after conflict resolution."""
        if not (commit := self.project.cherrypickhead):
            raise NoUpdateInProgressError()

        self.project.commit(
            message=commit.message,
            author=commit.author,
            committer=self.project.default_signature,
        )

    def abortupdate(self) -> None:
        """Abort an update with conflicts."""
        if not self.project.cherrypickhead:
            raise NoUpdateInProgressError()

        self.project.resetcherrypick()
