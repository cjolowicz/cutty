"""Command-line interface for creating projects from Cookiecutter templates."""
import pathlib
from typing import Optional

import click

from cutty.entrypoints.cli.cookiecutter import extra_context_callback
from cutty.entrypoints.cli.errors import fatal
from cutty.services.create import create as service_create
from cutty.variables.domain.bindings import Binding


@click.command()
@click.argument("template")
@click.argument("extra-context", nargs=-1, callback=extra_context_callback)
@click.option(
    "--non-interactive",
    is_flag=True,
    default=False,
    help="Do not prompt for template variables.",
)
@click.option(
    "--revision",
    metavar="REV",
    help="Branch, tag, or commit hash of the template repository.",
)
@click.option(
    "-C",
    "--cwd",
    metavar="DIR",
    type=click.Path(file_okay=False, dir_okay=True, path_type=pathlib.Path),
    help="Parent directory of the generated project.",
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
    "-i",
    "--in-place",
    is_flag=True,
    default=False,
    help="Strip the leading path component from generated files.",
)
@fatal
def create(
    template: str,
    extra_context: dict[str, str],
    non_interactive: bool,
    revision: Optional[str],
    cwd: Optional[pathlib.Path],
    template_directory: Optional[pathlib.Path],
    in_place: bool,
) -> None:
    """Generate projects from Cookiecutter templates."""
    extrabindings = [Binding(key, value) for key, value in extra_context.items()]

    if cwd is None:
        cwd = pathlib.Path.cwd()

    service_create(
        template,
        cwd,
        extrabindings=extrabindings,
        interactive=not non_interactive,
        revision=revision,
        directory=template_directory,
        in_place=in_place,
    )
