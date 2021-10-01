"""Project repositories."""
from pathlib import Path

import pygit2

from cutty.projects.common import createcommitmessage
from cutty.projects.common import GenerateProject
from cutty.projects.common import LATEST_BRANCH
from cutty.projects.common import linkcommitmessage
from cutty.projects.common import UPDATE_BRANCH
from cutty.projects.common import updatecommitmessage
from cutty.projects.loadtemplate import TemplateMetadata
from cutty.templates.adapters.cookiecutter.projectconfig import PROJECT_CONFIG_FILE
from cutty.util.git import Branch
from cutty.util.git import Repository


class ProjectRepository:
    """Project repository."""

    def __init__(self, path: Path) -> None:
        """Initialize."""
        self.project = Repository.open(path)

    @classmethod
    def create(cls, projectdir: Path, template: TemplateMetadata) -> None:
        """Initialize the git repository for a project."""
        try:
            project = Repository.open(projectdir)
        except pygit2.GitError:
            project = Repository.init(projectdir)

        project.commit(message=createcommitmessage(template))
        project.heads[LATEST_BRANCH] = project.head.commit

    def update(
        self, generateproject: GenerateProject, template: TemplateMetadata
    ) -> None:
        """Update a project by applying changes between the generated trees."""
        latestbranch = self.project.branch(LATEST_BRANCH)
        updatebranch = self.project.heads.create(
            UPDATE_BRANCH, latestbranch.commit, force=True
        )

        with self.project.worktree(updatebranch, checkout=False) as worktree:
            generateproject(worktree)
            Repository.open(worktree).commit(message=updatecommitmessage(template))

        self.project.cherrypick(updatebranch.commit)

        latestbranch.commit = updatebranch.commit

    def continueupdate(self) -> None:
        """Continue an update after conflict resolution."""
        if commit := self.project.cherrypickhead:
            self.project.commit(
                message=commit.message,
                author=commit.author,
                committer=self.project.default_signature,
            )

        self.project.heads[LATEST_BRANCH] = self.project.heads[UPDATE_BRANCH]

    def skipupdate(self) -> None:
        """Skip an update with conflicts."""
        self.project.resetcherrypick()
        self.project.heads[LATEST_BRANCH] = self.project.heads[UPDATE_BRANCH]

    def abortupdate(self) -> None:
        """Abort an update with conflicts."""
        self.project.resetcherrypick()
        self.project.heads[UPDATE_BRANCH] = self.project.heads[LATEST_BRANCH]

    def link(
        self,
        generateproject: GenerateProject,
        template: TemplateMetadata,
    ) -> None:
        """Link a project to a project template."""
        if latest := self.project.heads.get(LATEST_BRANCH):
            update = self.project.heads.create(UPDATE_BRANCH, latest, force=True)
        else:
            # Unborn branches cannot have worktrees. Create an orphan branch with an
            # empty placeholder commit instead. We'll squash it after project creation.
            update = _create_orphan_branch(self.project, UPDATE_BRANCH)

        with self.project.worktree(update, checkout=False) as worktree:
            generateproject(worktree)
            message = (
                createcommitmessage(template)
                if latest is None
                else updatecommitmessage(template)
            )
            Repository.open(worktree).commit(message=message)

        if latest is None:
            # Squash the empty initial commit.
            _squash_branch(self.project, update)

        (self.project.path / PROJECT_CONFIG_FILE).write_bytes(
            (update.commit.tree / PROJECT_CONFIG_FILE).data
        )

        self.project.commit(
            message=linkcommitmessage(template),
            author=update.commit.author,
            committer=self.project.default_signature,
        )

        self.project.heads[LATEST_BRANCH] = update.commit


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
