"""Linking projects to their templates."""
from cutty.projects.create import CreateProject
from cutty.projects.create import LATEST_BRANCH
from cutty.projects.create import UPDATE_BRANCH
from cutty.repositories.domain.repository import Repository as Template
from cutty.templates.adapters.cookiecutter.projectconfig import PROJECT_CONFIG_FILE
from cutty.util.git import Branch
from cutty.util.git import Repository


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


def linkproject(project: Repository, createproject: CreateProject) -> None:
    """Link a project to a Cookiecutter template."""
    if latest := project.heads.get(LATEST_BRANCH):
        update = project.heads.create(UPDATE_BRANCH, latest, force=True)
    else:
        # Unborn branches cannot have worktrees. Create an orphan branch with an
        # empty placeholder commit instead. We'll squash it after project creation.
        update = _create_orphan_branch(project, UPDATE_BRANCH)

    with project.worktree(update, checkout=False) as worktree:
        template = createproject(worktree)
        Repository.open(worktree).commit(
            message=_commitmessage(template, action="update" if latest else "import")
        )

    if latest is None:
        # Squash the empty initial commit.
        _squash_branch(project, update)

    (project.path / PROJECT_CONFIG_FILE).write_bytes(
        (update.commit.tree / PROJECT_CONFIG_FILE).data
    )

    project.commit(
        message=_commitmessage(template, action="link"),
        author=update.commit.author,
        committer=project.default_signature,
    )

    project.heads[LATEST_BRANCH] = update.commit


def _commitmessage(template: Template, action: str) -> str:
    if action == "link":
        return (
            f"Link to {template.name} {template.revision}"
            if template.revision
            else f"Link to {template.name}"
        )

    if action == "update":
        return (
            f"Update {template.name} to {template.revision}"
            if template.revision
            else f"Update {template.name}"
        )

    return (
        f"Initial import from {template.name} {template.revision}"
        if template.revision
        else f"Initial import from {template.name}"
    )
