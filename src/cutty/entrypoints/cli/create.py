"""Command-line interface for creating projects from Cookiecutter templates."""
import pathlib
from typing import Iterator
from typing import Optional

import click

from cutty.services.create import create as service_create
from cutty.templates.domain.bindings import Binding


def extra_context_callback(
    context: click.Context, parameter: click.Parameter, args: tuple[str, ...]
) -> dict[str, str]:
    """Callback for the EXTRA_CONTEXT argument."""

    def _generate() -> Iterator[tuple[str, str]]:
        for arg in args:
            try:
                key, value = arg.split("=", 1)
                yield key, value
            except ValueError:
                raise click.BadParameter(
                    "EXTRA_CONTEXT should contain items of the form key=value; "
                    f"'{arg}' doesn't match that form"
                )

    return dict(_generate())


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
    no_input: bool,
    checkout: Optional[str],
    output_dir: Optional[pathlib.Path],
    directory: Optional[pathlib.Path],
    overwrite_if_exists: bool,
    skip_if_file_exists: bool,
    in_place: bool,
) -> None:
    """Generate projects from Cookiecutter templates."""
    extrabindings = [Binding(key, value) for key, value in extra_context.items()]
    service_create(
        template,
        extrabindings=extrabindings,
        no_input=no_input,
        checkout=checkout,
        outputdir=output_dir,
        directory=pathlib.PurePosixPath(directory) if directory is not None else None,
        overwrite_if_exists=overwrite_if_exists,
        skip_if_file_exists=skip_if_file_exists,
        outputdirisproject=in_place,
    )
