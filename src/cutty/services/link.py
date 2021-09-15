"""Link a project to a Cookiecutter template."""
import contextlib
import pathlib
from collections.abc import Sequence
from typing import Optional

from cutty.filestorage.adapters.observers.git import LATEST_BRANCH
from cutty.filestorage.adapters.observers.git import UPDATE_BRANCH
from cutty.services.create import create
from cutty.templates.adapters.cookiecutter.projectconfig import PROJECT_CONFIG_FILE
from cutty.templates.adapters.cookiecutter.projectconfig import readcookiecutterjson
from cutty.templates.domain.bindings import Binding
from cutty.util.git import Repository


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

    assert template is not None  # noqa: S101

    latest = project.heads.setdefault(LATEST_BRANCH, project.head.commit)
    update = project.heads.create(UPDATE_BRANCH, latest, force=True)
    # XXX orphan branch would be better

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

    (project.path / PROJECT_CONFIG_FILE).write_bytes(
        (update.commit.tree / PROJECT_CONFIG_FILE).data
    )

    project.commit(
        message=update.commit.message,
        author=update.commit.author,
        committer=project.default_signature,
    )

    project.heads[LATEST_BRANCH] = update.commit
