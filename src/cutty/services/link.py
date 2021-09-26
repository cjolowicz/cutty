"""Link a project to a Cookiecutter template."""
import contextlib
import pathlib
from collections.abc import Callable
from collections.abc import Sequence
from typing import Optional

from cutty.errors import CuttyError
from cutty.repositories.domain.repository import Repository as Template
from cutty.services.create import create
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


CreateProject = Callable[[pathlib.Path], Template]


def link(
    template: Optional[str],
    projectdir: pathlib.Path,
    /,
    *,
    extrabindings: Sequence[Binding] = (),
    no_input: bool = False,
    checkout: Optional[str] = None,
    directory: Optional[pathlib.PurePosixPath] = None,
) -> None:
    """Link project to a Cookiecutter template."""
    project = Repository.open(projectdir)

    with contextlib.suppress(FileNotFoundError):
        projectconfig = readcookiecutterjson(project.path)
        extrabindings = list(projectconfig.bindings) + list(extrabindings)

        if template is None:
            template = projectconfig.template

    if template is None:
        raise TemplateNotSpecifiedError()

    def createproject(outputdir: pathlib.Path) -> Template:
        assert template is not None  # noqa: S101

        _, template2 = create(
            template,
            outputdir,
            outputdirisproject=True,
            extrabindings=extrabindings,
            no_input=no_input,
            checkout=checkout,
            directory=directory,
        )
        return template2

    linkproject(project, createproject)


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
            message=_commitmessage(
                template, "update" if latest is not None else "import"
            )
        )

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


def _commitmessage(template: Template, action: str) -> str:
    if action == "update" and template.revision:
        return f"Update {template.name} to {template.revision}"

    if action == "update":
        return f"Update {template.name}"

    if template.revision:
        return f"Initial import from {template.name} {template.revision}"

    return f"Initial import from {template.name}"
