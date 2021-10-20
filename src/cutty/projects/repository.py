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
    def create(cls, projectdir: Path, template: Template.Metadata) -> None:
        """Initialize the git repository for a project."""
        cls.create(projectdir, template)

    @classmethod
    def create2(cls, projectdir: Path, template: Template.Metadata) -> None:
        """Initialize the git repository for a project."""
        try:
            repository = cls(projectdir)
        except pygit2.GitError:
            Repository.init(projectdir)
            repository = cls(projectdir)

        if repository.project._repository.head_is_unborn:
            repository.createroot()

        repository.project.commit(message=createcommitmessage(template))

    @property
    def root(self) -> str:
        """Create an empty root commit."""
        return self.createroot(updateref=None)

    def createroot(self, *, updateref: Optional[str] = "HEAD") -> str:
        """Create an empty root commit."""
        author = committer = self.project.default_signature
        repository = self.project._repository
        tree = repository.TreeBuilder().write()
        oid = repository.create_commit(updateref, author, committer, "", tree, [])
        return str(oid)

    @contextmanager
    def build(self, *, parent: str) -> Iterator[ProjectBuilder]:
        """Create a commit with a generated project."""
        branch = self.project.heads.create(
            UPDATE_BRANCH, self.project._repository[parent], force=True
        )

        with self.project.worktree(branch, checkout=False) as worktree:
            builder = ProjectBuilder(worktree)
            yield builder

        self.project.heads.pop(branch.name)

    def link(self, message: str, *, commit: str) -> None:
        """Update the project configuration."""
        commit2 = self.project._repository[commit]

        (self.project.path / PROJECT_CONFIG_FILE).write_bytes(
            (commit2.tree / PROJECT_CONFIG_FILE).data
        )

        self.project.commit(
            message=message,
            author=commit2.author,
            committer=self.project.default_signature,
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

    def skipupdate(self) -> None:
        """Skip an update with conflicts."""
        if not (commit := self.project.cherrypickhead):
            raise NoUpdateInProgressError()

        self.project.resetcherrypick()
        self.link(f"Skip: {commit.message}", commit=str(commit.id))

    def abortupdate(self) -> None:
        """Abort an update with conflicts."""
        if not self.project.cherrypickhead:
            raise NoUpdateInProgressError()

        self.project.resetcherrypick()


def createcommitmessage(template: Template.Metadata) -> str:
    """Return the commit message for importing the template."""
    if template.revision:
        return f"Initial import from {template.name} {template.revision}"
    else:
        return f"Initial import from {template.name}"


def updatecommitmessage(template: Template.Metadata) -> str:
    """Return the commit message for updating the template."""
    if template.revision:
        return f"Update {template.name} to {template.revision}"
    else:
        return f"Update {template.name}"


def linkcommitmessage(template: Template.Metadata) -> str:
    """Return the commit message for linking the template."""
    if template.revision:
        return f"Link to {template.name} {template.revision}"
    else:
        return f"Link to {template.name}"
