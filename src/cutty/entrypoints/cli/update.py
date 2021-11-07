"""Command-line interface for updating projects from Cookiecutter templates."""
import pathlib
from typing import Optional

import click

from cutty.entrypoints.cli.cookiecutter import extra_context_callback
from cutty.entrypoints.cli.errors import fatal
from cutty.projects.repository import ProjectRepository
from cutty.services.update import update as service_update
from cutty.variables.domain.bindings import Binding


@click.command()
@click.argument("extra-context", nargs=-1, callback=extra_context_callback)
@click.option(
    "--non-interactive",
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
    "--revision",
    metavar="REV",
    help="Branch, tag, or commit hash of the template repository.",
)
@click.option(
    "--template-directory",
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
    "--abort",
    is_flag=True,
    default=False,
    help="Abort the current update.",
)
@fatal
def update(
    extra_context: dict[str, str],
    non_interactive: bool,
    cwd: Optional[pathlib.Path],
    revision: Optional[str],
    template_directory: Optional[pathlib.Path],
    continue_: bool,
    abort: bool,
) -> None:
    """Update a project with changes from its template."""
    if cwd is None:
        cwd = pathlib.Path.cwd()

    project = ProjectRepository(cwd)

    if continue_:
        project.continue_()
        return

    if abort:
        project.abort()
        return

    extrabindings = [Binding(key, value) for key, value in extra_context.items()]

    service_update(
        cwd,
        extrabindings=extrabindings,
        interactive=not non_interactive,
        revision=revision,
        directory=template_directory,
    )
