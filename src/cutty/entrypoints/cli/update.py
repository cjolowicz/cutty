"""Command-line interface for updating projects from Cookiecutter templates."""
import pathlib
from typing import Optional

import click

from cutty.entrypoints.cli.cookiecutter import extra_context_callback
from cutty.projects.repository import ProjectRepository
from cutty.services.update import update as service_update
from cutty.templates.domain.bindings import Binding


@click.argument("extra-context", nargs=-1, callback=extra_context_callback)
@click.option(
    "--no-input",
    is_flag=True,
    default=False,
    help="Do not prompt for template variables.",
)
@click.option(
    "-C",
    "--cwd",
    metavar="DIR",
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True, path_type=pathlib.Path
    ),
    help="Directory of the generated project.",
)
@click.option(
    "-c",
    "--checkout",
    metavar="REV",
    help="Branch, tag, or commit hash of the template repository.",
)
@click.option(
    "--directory",
    metavar="DIR",
    type=click.Path(path_type=pathlib.Path),
    help=(
        "Directory within the template repository that contains the "
        "cookiecutter.json file."
    ),
)
@click.option(
    "continue_",
    "--continue",
    is_flag=True,
    default=False,
    help="Resume updating after conflict resolution.",
)
@click.option(
    "--skip",
    is_flag=True,
    default=False,
    help="Skip the current update.",
)
@click.option(
    "--abort",
    is_flag=True,
    default=False,
    help="Abort the current update.",
)
def update(
    extra_context: dict[str, str],
    no_input: bool,
    cwd: Optional[pathlib.Path],
    checkout: Optional[str],
    directory: Optional[pathlib.Path],
    continue_: bool,
    skip: bool,
    abort: bool,
) -> None:
    """Update a project with changes from its template."""
    if cwd is None:
        cwd = pathlib.Path.cwd()

    project = ProjectRepository(cwd)

    if continue_:
        project.continueupdate()
        return

    if skip:
        project.skipupdate()
        return

    if abort:
        project.abortupdate()
        return

    extrabindings = [Binding(key, value) for key, value in extra_context.items()]

    service_update(
        cwd,
        extrabindings=extrabindings,
        interactive=not no_input,
        checkout=checkout,
        directory=pathlib.PurePosixPath(directory) if directory is not None else None,
    )
