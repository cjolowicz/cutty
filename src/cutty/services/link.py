"""Link a project to a Cookiecutter template."""
import contextlib
import pathlib
from collections.abc import Sequence
from typing import Optional

from cutty.errors import CuttyError
from cutty.services.create import create
from cutty.services.git import creategitrepository
from cutty.services.git import LATEST_BRANCH
from cutty.services.git import UPDATE_BRANCH
from cutty.templates.adapters.cookiecutter.projectconfig import PROJECT_CONFIG_FILE
from cutty.templates.adapters.cookiecutter.projectconfig import readcookiecutterjson
from cutty.templates.domain.bindings import Binding
from cutty.util.git import Branch
from cutty.util.git import Repository


class TemplateNotSpecifiedError(CuttyError):
    """The template was not specified."""


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


def _transform_commit_message(message: str) -> str:
    if message.startswith("Update"):
        return message.replace(" to ", " ").replace("Update ", "Link to ")
    return message.replace("Initial import from ", "Link to ")


def link(
    template: Optional[str] = None,
    /,
    *,
    extrabindings: Sequence[Binding] = (),
    no_input: bool = False,
    checkout: Optional[str] = None,
    directory: Optional[pathlib.PurePosixPath] = None,
    projectdir: Optional[pathlib.Path] = None,
) -> None:
    """Link project to a Cookiecutter template."""
    if projectdir is None:
        projectdir = pathlib.Path.cwd()

    project = Repository.open(projectdir)

    with contextlib.suppress(FileNotFoundError):
        projectconfig = readcookiecutterjson(project.path)
        extrabindings = list(projectconfig.bindings) + list(extrabindings)

        if template is None:
            template = projectconfig.template

    if template is None:
        raise TemplateNotSpecifiedError()

    if latest := project.heads.get(LATEST_BRANCH):
        update = project.heads.create(UPDATE_BRANCH, latest, force=True)
    else:
        # Unborn branches cannot have worktrees. Create an orphan branch with an
        # empty placeholder commit instead. We'll squash it after project creation.
        update = _create_orphan_branch(project, UPDATE_BRANCH)

    with project.worktree(update, checkout=False) as worktree:
        project_dir, template2 = create(
            template,
            worktree,
            outputdirisproject=True,
            extrabindings=extrabindings,
            no_input=no_input,
            checkout=checkout,
            directory=directory,
        )
        creategitrepository(project_dir, template2.name, template2.revision)

    if latest is None:
        # Squash the empty initial commit.
        _squash_branch(project, update)

    (project.path / PROJECT_CONFIG_FILE).write_bytes(
        (update.commit.tree / PROJECT_CONFIG_FILE).data
    )

    message = _transform_commit_message(update.commit.message)
    project.commit(
        message=message,
        author=update.commit.author,
        committer=project.default_signature,
    )

    project.heads[LATEST_BRANCH] = update.commit
