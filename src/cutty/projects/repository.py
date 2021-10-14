"""Project repositories."""
from collections.abc import Callable
from collections.abc import Iterator
from pathlib import Path

import pygit2

from cutty.compat.contextlib import contextmanager
from cutty.errors import CuttyError
from cutty.projects.projectconfig import PROJECT_CONFIG_FILE
from cutty.projects.template import Template
from cutty.util.git import Branch
from cutty.util.git import Repository


UPDATE_BRANCH = "cutty/update"


class NoUpdateInProgressError(CuttyError):
    """A sequencer action was invoked without an update in progress."""


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
    def reset(
        self, template: Template.Metadata
    ) -> Iterator[tuple[Path, Callable[[], pygit2.Commit]]]:
        """Create an orphan commit with a generated project."""
        # Unborn branches cannot have worktrees.
        branch = _create_orphan_branch(self.project, UPDATE_BRANCH)

        with self.project.worktree(branch, checkout=False) as worktree:
            yield worktree.path, lambda: latest
            message = _createcommitmessage(template)
            worktree.commit(message=message)

        latest = self.project.heads.pop(branch.name)

    @contextmanager
    def link(self, template: Template.Metadata) -> Iterator[Path]:
        """Link a project to a project template."""
        with self.reset(template) as (path, getlatest):
            yield path

        self.updateconfig(message=_linkcommitmessage(template), commit=getlatest())

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
        branch = self.project.heads.create(UPDATE_BRANCH, parent, force=True)

        with self.project.worktree(branch, checkout=False) as worktree:
            yield worktree.path
            worktree.commit(message=_updatecommitmessage(template))

        commit = self.project.heads.pop(branch.name)

        if commit != parent:
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


def _create_orphan_commit(repository: Repository) -> pygit2.Commit:
    """Create an orphan empty commit."""
    author = committer = repository.default_signature
    oid = repository._repository.create_commit(
        None,
        author,
        committer,
        "initial",
        repository._repository.TreeBuilder().write(),
        [],
    )
    commit: pygit2.Commit = repository._repository[oid]
    return commit


def _create_orphan_branch(repository: Repository, name: str) -> Branch:
    """Create an orphan branch with an empty commit."""
    commit = _create_orphan_commit(repository)
    return repository.heads.create(name, commit, force=True)


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
