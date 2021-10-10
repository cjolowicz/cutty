"""Command-line interface for creating projects from Cookiecutter templates."""
import pathlib
from typing import Optional

import click

from cutty.entrypoints.cli.cookiecutter import extra_context_callback
from cutty.entrypoints.cli.cookiecutter import fileexistspolicy
from cutty.services.create import createproject
from cutty.templates.domain.bindings import Binding


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
    "-o",
    "--output-dir",
    metavar="DIR",
    type=click.Path(file_okay=False, dir_okay=True, path_type=pathlib.Path),
    help="Parent directory of the generated project.",
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
    "-f",
    "--overwrite-if-exists",
    is_flag=True,
    default=False,
    help="Overwrite the contents of the output directory if it already exists.",
)
@click.option(
    "-s",
    "--skip-if-file-exists",
    is_flag=True,
    default=False,
    help="Skip the files in the corresponding directories if they already exist.",
)
@click.option(
    "-i",
    "--in-place",
    is_flag=True,
    default=False,
    help="Strip the leading path component from generated files.",
)
def create(
    template: str,
    extra_context: dict[str, str],
    non_interactive: bool,
    revision: Optional[str],
    output_dir: Optional[pathlib.Path],
    directory: Optional[pathlib.Path],
    overwrite_if_exists: bool,
    skip_if_file_exists: bool,
    in_place: bool,
) -> None:
    """Generate projects from Cookiecutter templates."""
    extrabindings = [Binding(key, value) for key, value in extra_context.items()]

    if output_dir is None:
        output_dir = pathlib.Path.cwd()

    fileexists = fileexistspolicy(overwrite_if_exists, skip_if_file_exists)
    createproject(
        template,
        output_dir,
        extrabindings=extrabindings,
        interactive=not non_interactive,
        revision=revision,
        directory=directory,
        fileexists=fileexists,
        in_place=in_place,
    )
