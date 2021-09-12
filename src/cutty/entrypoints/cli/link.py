"""Command-line interface for linking projects to a Cookiecutter template."""
import pathlib
from typing import Optional

import click

from cutty.entrypoints.cli.create import extra_context_callback
from cutty.services.link import link as service_link
from cutty.templates.domain.bindings import Binding


@click.argument("template")
@click.argument("extra-context", nargs=-1, callback=extra_context_callback)
@click.option(
    "-C",
    "--cwd",
    metavar="DIR",
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True, path_type=pathlib.Path
    ),
    help="Directory of the generated project.",
)
def link(
    template: str, extra_context: dict[str, str], cwd: Optional[pathlib.Path]
) -> None:
    """Link project to a Cookiecutter template."""
    extrabindings = [Binding(key, value) for key, value in extra_context.items()]
    service_link(template, extrabindings=extrabindings, projectdir=cwd)
