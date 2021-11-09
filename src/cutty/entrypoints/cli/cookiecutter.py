"""Command-line interface for creating projects from Cookiecutter templates."""
from collections.abc import Iterator
from pathlib import Path
from typing import Optional

import click

from cutty.entrypoints.cli.errors import fatal
from cutty.filestorage.adapters.disk import FileExistsPolicy
from cutty.services.cookiecutter import create
from cutty.variables.domain.bindings import Binding


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


def fileexistspolicy(
    overwrite_if_exists: bool, skip_if_file_exists: bool
) -> FileExistsPolicy:
    """Return the policy for overwriting existing files."""
    return (
        FileExistsPolicy.RAISE
        if not overwrite_if_exists
        else FileExistsPolicy.SKIP
        if skip_if_file_exists
        else FileExistsPolicy.OVERWRITE
    )


@click.command()
@click.argument("location", metavar="TEMPLATE")
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
@fatal
def cookiecutter(
    location: str,
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

    if output_dir is None:
        output_dir = Path.cwd()

    fileexists = fileexistspolicy(overwrite_if_exists, skip_if_file_exists)

    create(
        location,
        output_dir,
        extrabindings=extrabindings,
        interactive=not no_input,
        checkout=checkout,
        directory=directory,
        fileexists=fileexists,
    )
