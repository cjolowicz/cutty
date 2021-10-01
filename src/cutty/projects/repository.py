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
from cutty.projects.update import abortupdate
from cutty.projects.update import skipupdate
from cutty.templates.adapters.cookiecutter.projectconfig import PROJECT_CONFIG_FILE
from cutty.util import git
from cutty.util.git import Branch
from cutty.util.git import Repository


class ProjectRepository:
    """Project repository."""

    def __init__(self, path: Path) -> None:
        """Initialize."""
        self.path = path

    @classmethod
    def create(cls, projectdir: Path, template: TemplateMetadata) -> None:
        """Initialize the git repository for a project."""
        try:
            project = git.Repository.open(projectdir)
        except pygit2.GitError:
            project = git.Repository.init(projectdir)

        project.commit(message=createcommitmessage(template))
        project.heads[LATEST_BRANCH] = project.head.commit

    def update(
        self, generateproject: GenerateProject, template: TemplateMetadata
    ) -> None:
        """Update a project by applying changes between the generated trees."""
        project = Repository.open(self.path)

        latestbranch = project.branch(LATEST_BRANCH)
        updatebranch = project.heads.create(
            UPDATE_BRANCH, latestbranch.commit, force=True
        )

        with project.worktree(updatebranch, checkout=False) as worktree:
            generateproject(worktree)
            Repository.open(worktree).commit(message=updatecommitmessage(template))

        project.cherrypick(updatebranch.commit)

        latestbranch.commit = updatebranch.commit

    def continueupdate(self) -> None:
        """Continue an update after conflict resolution."""
        project = Repository.open(self.path)

        if commit := project.cherrypickhead:
            project.commit(
                message=commit.message,
                author=commit.author,
                committer=project.default_signature,
            )

        project.heads[LATEST_BRANCH] = project.heads[UPDATE_BRANCH]

    def skipupdate(self) -> None:
        """Skip an update with conflicts."""
        skipupdate(self.path)

    def abortupdate(self) -> None:
        """Abort an update with conflicts."""
        abortupdate(self.path)

    def link(
        self,
        generateproject: GenerateProject,
        template: TemplateMetadata,
    ) -> None:
        """Link a project to a project template."""
        project = Repository.open(self.path)

        if latest := project.heads.get(LATEST_BRANCH):
            update = project.heads.create(UPDATE_BRANCH, latest, force=True)
        else:
            # Unborn branches cannot have worktrees. Create an orphan branch with an
            # empty placeholder commit instead. We'll squash it after project creation.
            update = _create_orphan_branch(project, UPDATE_BRANCH)

        with project.worktree(update, checkout=False) as worktree:
            generateproject(worktree)
            message = (
                createcommitmessage(template)
                if latest is None
                else updatecommitmessage(template)
            )
            Repository.open(worktree).commit(message=message)

        if latest is None:
            # Squash the empty initial commit.
            _squash_branch(project, update)

        (project.path / PROJECT_CONFIG_FILE).write_bytes(
            (update.commit.tree / PROJECT_CONFIG_FILE).data
        )

        project.commit(
            message=linkcommitmessage(template),
            author=update.commit.author,
            committer=project.default_signature,
        )

        project.heads[LATEST_BRANCH] = update.commit


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
