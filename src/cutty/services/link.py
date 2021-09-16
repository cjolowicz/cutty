"""Link a project to a Cookiecutter template."""
import contextlib
import pathlib
from collections.abc import Sequence
from typing import Optional

import pygit2

from cutty.errors import CuttyError
from cutty.filestorage.adapters.observers.git import LATEST_BRANCH
from cutty.filestorage.adapters.observers.git import UPDATE_BRANCH
from cutty.services.create import create
from cutty.templates.adapters.cookiecutter.projectconfig import PROJECT_CONFIG_FILE
from cutty.templates.adapters.cookiecutter.projectconfig import readcookiecutterjson
from cutty.templates.domain.bindings import Binding
from cutty.util.git import Repository


class TemplateNotSpecifiedError(CuttyError):
    """The template was not specified."""


def _create_empty_orphan_commit(project: Repository) -> pygit2.Commit:
    """Create an empty commit without parents."""
    author = committer = project.default_signature
    repository = project._repository
    oid = repository.TreeBuilder().write()
    oid = repository.create_commit(None, author, committer, "initial", oid, [])
    return repository[oid]


def _copy_to_orphan_commit(project: Repository, commit: pygit2.Commit) -> pygit2.Commit:
    """Copy the given commit, except for its parent."""
    repository = project._repository
    oid = repository.create_commit(
        None,
        commit.author,
        commit.committer,
        commit.message,
        commit.tree.id,
        [],
    )
    return repository[oid]


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
        commit = _create_empty_orphan_commit(project)
        update = project.heads.create(UPDATE_BRANCH, commit)

    with project.worktree(update, checkout=False) as worktree:
        create(
            template,
            outputdir=worktree,
            outputdirisproject=True,
            extrabindings=extrabindings,
            no_input=no_input,
            checkout=checkout,
            directory=directory,
        )

    if latest is None:
        # Squash the empty initial commit.
        update.commit = _copy_to_orphan_commit(project, update.commit)

    (project.path / PROJECT_CONFIG_FILE).write_bytes(
        (update.commit.tree / PROJECT_CONFIG_FILE).data
    )

    project.commit(
        message=update.commit.message,
        author=update.commit.author,
        committer=project.default_signature,
    )

    project.heads[LATEST_BRANCH] = update.commit
