"""Project repositories."""
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
    message: str = ""
    _commit: Optional[pygit2.Commit] = None
    _commit2: Optional[str] = None

    @property
    def commit2(self) -> str:
        """Return the ID of the newly created commit."""
        assert self._commit is not None  # noqa: S101
        return str(self._commit.id)

    @property
    def commit(self) -> pygit2.Commit:
        """Return the newly created commit."""
        assert self._commit is not None  # noqa: S101
        return self._commit

    @commit.setter
    def commit(self, commit: pygit2.Commit) -> None:
        """Set the newly created commit."""
        self._commit = commit
        self._commit2 = str(commit.id)


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
        with self.build(str(self.root.id)) as builder:
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
    def build(self, parent2: str) -> Iterator[ProjectBuilder]:
        """Create a commit with a generated project."""
        parent = self.project._repository[parent2]
        branch = self.project.heads.create(UPDATE_BRANCH, parent, force=True)

        with self.project.worktree(branch, checkout=False) as worktree:
            builder = ProjectBuilder(worktree.path)
            yield builder

            worktree.commit(message=builder.message)

        builder.commit = self.project.heads.pop(branch.name)

    @contextmanager
    def link(self, template: Template.Metadata) -> Iterator[Path]:
        """Link a project to a project template."""
        with self.reset(template) as builder:
            yield builder.path

        commit = self.project._repository[builder.commit2]
        self.updateconfig(message=_linkcommitmessage(template), commit=commit)

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
        with self.update2(template, parent=str(parent.id)) as path:
            yield path

    @contextmanager
    def update2(self, template: Template.Metadata, *, parent: str) -> Iterator[Path]:
        """Update a project by applying changes between the generated trees."""
        parent2 = self.project._repository[parent]
        with self.build(str(parent2.id)) as builder:
            builder.message = _updatecommitmessage(template)
            yield builder.path

        commit = self.project._repository[builder.commit2]
        if commit != parent2:
            self.project.cherrypick(commit)

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
