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
    "--directory",
    metavar="DIR",
    type=click.Path(path_type=pathlib.Path),
    help=(
        "Directory within the template repository that contains the "
        "cookiecutter.json file."
    ),
)
def link(
    template: str,
    extra_context: dict[str, str],
    no_input: bool,
    cwd: Optional[pathlib.Path],
    directory: Optional[pathlib.Path],
) -> None:
    """Link project to a Cookiecutter template."""
    extrabindings = [Binding(key, value) for key, value in extra_context.items()]
    service_link(
        template,
        extrabindings=extrabindings,
        no_input=no_input,
        projectdir=cwd,
        directory=pathlib.PurePosixPath(directory) if directory is not None else None,
    )
