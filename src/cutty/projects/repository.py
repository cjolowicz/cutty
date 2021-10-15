"""Project repositories."""
from collections.abc import Callable
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pygit2

from cutty.compat.contextlib import contextmanager
from cutty.errors import CuttyError
from cutty.projects.projectconfig import PROJECT_CONFIG_FILE
from cutty.projects.template import Template
from cutty.util.git import Repository


UPDATE_BRANCH = "cutty/update"


class NoUpdateInProgressError(CuttyError):
    """A sequencer action was invoked without an update in progress."""


@dataclass
class ProjectBuilder:
    """Adding a project to the repository."""

    path: Path
    _getcommit: Callable[[], pygit2.Commit]
    message: str = ""
    _commit: Optional[pygit2.Commit] = None

    @property
    def commit(self) -> pygit2.Commit:
        """Return the newly created commit."""
        return self._getcommit()


class ProjectRepository:
    """Project repository."""

    def __init__(self, path: Path) -> None:
        """Initialize."""
        self.project = Repository.open(path)

    @classmethod
    def create(cls, projectdir: Path, template: Template.Metadata) -> None:
        """Initialize the git repository for a project."""
        try:
            project = Repository.open(projectdir)
        except pygit2.GitError:
            project = Repository.init(projectdir)

        project.commit(message=_createcommitmessage(template))

    @contextmanager
    def reset(self, template: Template.Metadata) -> Iterator[ProjectBuilder]:
        """Create an orphan commit with a generated project."""
        with self.build(self.root) as builder:
            builder.message = _createcommitmessage(template)
            yield builder

    @property
    def root(self) -> pygit2.Commit:
        """Create an orphan empty commit."""
        author = committer = self.project.default_signature
        repository = self.project._repository
        tree = repository.TreeBuilder().write()
        oid = repository.create_commit(None, author, committer, "", tree, [])
        commit: pygit2.Commit = repository[oid]
        return commit

    @contextmanager
    def build(self, parent: pygit2.Commit) -> Iterator[ProjectBuilder]:
        """Create a commit with a generated project."""
        branch = self.project.heads.create(UPDATE_BRANCH, parent, force=True)

        with self.project.worktree(branch, checkout=False) as worktree:
            builder = ProjectBuilder(worktree.path, lambda: commit)
            yield builder

            worktree.commit(message=builder.message)

        commit = self.project.heads.pop(branch.name)

    @contextmanager
    def link(self, template: Template.Metadata) -> Iterator[Path]:
        """Link a project to a project template."""
        with self.reset(template) as builder:
            yield builder.path

        self.updateconfig(message=_linkcommitmessage(template), commit=builder.commit)

    def updateconfig(self, message: str, *, commit: pygit2.Commit) -> None:
        """Update the project configuration."""
        (self.project.path / PROJECT_CONFIG_FILE).write_bytes(
            (commit.tree / PROJECT_CONFIG_FILE).data
        )

        self.project.commit(
            message=message,
            author=commit.author,
            committer=self.project.default_signature,
        )

    @contextmanager
    def update(
        self, template: Template.Metadata, *, parent: pygit2.Commit
    ) -> Iterator[Path]:
        """Update a project by applying changes between the generated trees."""
        with self.build(parent) as builder:
            builder.message = _updatecommitmessage(template)
            yield builder.path

        if builder.commit != parent:
            self.project.cherrypick(builder.commit)

    def continueupdate(self) -> None:
        """Continue an update after conflict resolution."""
        if not (commit := self.project.cherrypickhead):
            raise NoUpdateInProgressError()

        self.project.commit(
            message=commit.message,
            author=commit.author,
            committer=self.project.default_signature,
        )

    def skipupdate(self) -> None:
        """Skip an update with conflicts."""
        if not (commit := self.project.cherrypickhead):
            raise NoUpdateInProgressError()

        self.project.resetcherrypick()
        self.updateconfig(f"Skip: {commit.message}", commit=commit)

    def abortupdate(self) -> None:
        """Abort an update with conflicts."""
        if not self.project.cherrypickhead:
            raise NoUpdateInProgressError()

        self.project.resetcherrypick()


def _createcommitmessage(template: Template.Metadata) -> str:
    """Return the commit message for importing the template."""
    if template.revision:
        return f"Initial import from {template.name} {template.revision}"
    else:
        return f"Initial import from {template.name}"


def _updatecommitmessage(template: Template.Metadata) -> str:
    """Return the commit message for updating the template."""
    if template.revision:
        return f"Update {template.name} to {template.revision}"
    else:
        return f"Update {template.name}"


def _linkcommitmessage(template: Template.Metadata) -> str:
    """Return the commit message for linking the template."""
    if template.revision:
        return f"Link to {template.name} {template.revision}"
    else:
        return f"Link to {template.name}"
