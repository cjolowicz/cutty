"""Command-line interface for updating projects from Cookiecutter templates."""
import pathlib
from typing import Optional

import click

from cutty.entrypoints.cli._main import main as _main
from cutty.entrypoints.cli.create import extra_context_callback
from cutty.services.update import update as service_update
from cutty.templates.domain.bindings import Binding


@_main.command()
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
def update(
    extra_context: dict[str, str],
    no_input: bool,
    cwd: Optional[pathlib.Path],
) -> None:
    """Update a project with changes from its template."""
    extrabindings = [Binding(key, value) for key, value in extra_context.items()]
    service_update(extrabindings=extrabindings, no_input=no_input, projectdir=cwd)
