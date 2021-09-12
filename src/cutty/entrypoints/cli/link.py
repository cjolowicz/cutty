"""Command-line interface for linking projects to a Cookiecutter template."""
import pathlib
from typing import Optional

import click

from cutty.services.link import link as service_link


@click.argument("template")
@click.option(
    "-C",
    "--cwd",
    metavar="DIR",
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True, path_type=pathlib.Path
    ),
    help="Directory of the generated project.",
)
def link(template: str, cwd: Optional[pathlib.Path]) -> None:
    """Link project to a Cookiecutter template."""
    service_link(template, projectdir=cwd)
