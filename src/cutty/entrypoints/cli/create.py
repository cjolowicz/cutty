"""Command-line interface for creating projects from templates."""
import pathlib
from typing import Iterator
from typing import Optional

import click

import cutty.services.create


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


@click.command()
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
    type=click.Path(file_okay=False, dir_okay=True),
    help="Parent directory of the generated project.",
)
@click.option(
    "--directory",
    metavar="DIR",
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
@click.version_option()
def main(
    template: str,
    extra_context: dict[str, str],
    no_input: bool,
    checkout: Optional[str],
    output_dir: Optional[str],
    directory: Optional[str],
    overwrite_if_exists: bool,
    skip_if_file_exists: bool,
) -> None:
    """cutty."""
    cutty.services.create.main(
        template,
        extra_context=extra_context,
        no_input=no_input,
        checkout=checkout,
        output_dir=pathlib.Path(output_dir) if output_dir is not None else None,
        directory=pathlib.PurePosixPath(directory) if directory is not None else None,
        overwrite_if_exists=overwrite_if_exists,
        skip_if_file_exists=skip_if_file_exists,
    )
