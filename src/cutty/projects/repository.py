"""Project repositories."""
from collections.abc import Callable
from collections.abc import Iterator
from pathlib import Path

import pygit2

from cutty.compat.contextlib import contextmanager
from cutty.projects.projectconfig import PROJECT_CONFIG_FILE
from cutty.projects.template import Template
from cutty.util.git import Branch
from cutty.util.git import Repository


LATEST_BRANCH = "cutty/latest"
UPDATE_BRANCH = "cutty/update"


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
        project.heads[LATEST_BRANCH] = project.head.commit

    @contextmanager
    def reset(
        self, template: Template.Metadata
    ) -> Iterator[tuple[Path, Callable[[], pygit2.Commit]]]:
        """Create an orphan branch for project generation."""
        for name in (LATEST_BRANCH, UPDATE_BRANCH):
            self.project.heads.pop(name, None)

        # Unborn branches cannot have worktrees. Create an orphan branch with an
        # empty placeholder commit instead. We'll squash it after project creation.
        update = _create_orphan_branch(self.project, UPDATE_BRANCH)

        with self.project.worktree(update, checkout=False) as worktree:
            yield worktree.path, lambda: latest
            message = _createcommitmessage(template)
            worktree.commit(message=message)

        # Squash the empty initial commit.
        _squash_branch(self.project, update)

        latest = update.commit

    @contextmanager
    def link(self, template: Template.Metadata) -> Iterator[Path]:
        """Link a project to a project template."""
        with self.reset(template) as (path, _):
            yield path

        self.updateconfig(message=_linkcommitmessage(template))

    def updateconfig(self, message: str) -> None:
        """Update the project configuration."""
        update = self.project.branch(UPDATE_BRANCH)

        (self.project.path / PROJECT_CONFIG_FILE).write_bytes(
            (update.commit.tree / PROJECT_CONFIG_FILE).data
        )

        self.project.commit(
            message=message,
            author=update.commit.author,
            committer=self.project.default_signature,
        )

    @contextmanager
    def update(
        self, template: Template.Metadata, *, parent: pygit2.Commit
    ) -> Iterator[Path]:
        """Update a project by applying changes between the generated trees."""
        updatebranch = self.project.heads.create(UPDATE_BRANCH, parent, force=True)

        with self.project.worktree(updatebranch, checkout=False) as worktree:
            yield worktree.path
            worktree.commit(message=_updatecommitmessage(template))

        self.project.cherrypick(updatebranch.commit)

    def continueupdate(self) -> None:
        """Continue an update after conflict resolution."""
        if commit := self.project.cherrypickhead:
            self.project.commit(
                message=commit.message,
                author=commit.author,
                committer=self.project.default_signature,
            )

    def skipupdate(self) -> None:
        """Skip an update with conflicts."""
        self.project.resetcherrypick()
        self.updateconfig("Skip update")

    def abortupdate(self) -> None:
        """Abort an update with conflicts."""
        self.project.resetcherrypick()


def _create_orphan_branch(repository: Repository, name: str) -> Branch:
    """Create an orphan branch with an empty commit."""
    author = committer = repository.default_signature
    repository._repository.create_commit(
        f"refs/heads/{name}",
        author,
        committer,
        "initial",
        repository._repository.TreeBuilder().write(),
        [],
    )
    return repository.branch(name)


def _squash_branch(repository: Repository, branch: Branch) -> None:
    """Squash the branch."""
    name, commit = branch.name, branch.commit
    del repository.heads[name]
    repository._repository.create_commit(
        f"refs/heads/{name}",
        commit.author,
        commit.committer,
        commit.message,
        commit.tree.id,
        [],
    )


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
