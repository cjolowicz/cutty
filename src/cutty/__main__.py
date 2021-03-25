"""Command-line interface."""
import pathlib
from typing import Optional

import click

import cutty.application.cookiecutter.main


@click.command()
@click.argument("url")
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
    url: str,
    no_input: bool,
    checkout: Optional[str],
    output_dir: Optional[str],
    directory: Optional[str],
    overwrite_if_exists: bool,
    skip_if_file_exists: bool,
) -> None:
    """cutty."""
    cutty.application.cookiecutter.main.main(
        url,
        no_input=no_input,
        checkout=checkout,
        output_dir=pathlib.Path(output_dir) if output_dir is not None else None,
        directory=pathlib.PurePosixPath(directory) if directory is not None else None,
        overwrite_if_exists=overwrite_if_exists,
        skip_if_file_exists=skip_if_file_exists,
    )


if __name__ == "__main__":
    main(prog_name="cutty")  # pragma: no cover
