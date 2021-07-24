"""Command-line interface for creating projects from Cookiecutter templates."""
from pathlib import Path
from pathlib import PurePosixPath
from typing import Optional

import click

from cutty.entrypoints.cli.create import extra_context_callback
from cutty.services.create import create as service_create
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
    "-c",
    "--checkout",
    metavar="REV",
    help="Branch, tag, or commit hash of the template repository.",
)
@click.option(
    "-o",
    "--output-dir",
    metavar="DIR",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    help="Parent directory of the generated project.",
)
@click.option(
    "--directory",
    metavar="DIR",
    type=click.Path(path_type=Path),
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
def cookiecutter(
    template: str,
    extra_context: dict[str, str],
    no_input: bool,
    checkout: Optional[str],
    output_dir: Optional[Path],
    directory: Optional[Path],
    overwrite_if_exists: bool,
    skip_if_file_exists: bool,
) -> None:
    """Generate projects from Cookiecutter templates."""
    extrabindings = [Binding(key, value) for key, value in extra_context.items()]
    service_create(
        template,
        extrabindings=extrabindings,
        no_input=no_input,
        checkout=checkout,
        outputdir=output_dir,
        directory=PurePosixPath(directory) if directory is not None else None,
        overwrite_if_exists=overwrite_if_exists,
        skip_if_file_exists=skip_if_file_exists,
        createrepository=False,
        createconfigfile=False,
    )
