"""Command-line interface for importing changesets into projects."""
from pathlib import Path
from typing import Optional

import click

from cutty.entrypoints.cli.cookiecutter import extra_context_callback
from cutty.entrypoints.cli.errors import fatal
from cutty.projects.repository import ProjectRepository
from cutty.services.import_ import import_ as service
from cutty.variables.domain.bindings import Binding


@click.command("import")
@click.option(
    "--revision",
    metavar="REV",
    help="Branch, tag, or commit hash of the template repository.",
)
@click.option(
    "-C",
    "--cwd",
    metavar="DIR",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Directory of the generated project.",
)
@click.option(
    "--non-interactive",
    is_flag=True,
    default=False,
    help="Do not prompt for template variables.",
)
@click.option(
    "--template-directory",
    metavar="DIR",
    type=click.Path(path_type=Path),
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
    help="Resume importing after conflict resolution.",
)
@click.option(
    "--abort",
    is_flag=True,
    default=False,
    help="Abort the current update.",
)
@click.argument("extra-context", nargs=-1, callback=extra_context_callback)
@fatal
def import_(
    revision: Optional[str],
    extra_context: dict[str, str],
    cwd: Optional[Path],
    non_interactive: bool,
    template_directory: Optional[Path],
    continue_: bool,
    abort: bool,
) -> None:
    """Import changesets from templates into projects."""
    if cwd is None:
        cwd = Path.cwd()

    project = ProjectRepository(cwd)

    if continue_:
        project.continue_()
        return

    if abort:
        project.abort()
        return

    extrabindings = [Binding(key, value) for key, value in extra_context.items()]

    service(
        cwd,
        revision=revision,
        extrabindings=extrabindings,
        interactive=not non_interactive,
        directory=template_directory,
    )
