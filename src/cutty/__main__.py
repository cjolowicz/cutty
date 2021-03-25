"""Command-line interface."""
import pathlib
from typing import Optional

import click

import cutty.application.cookiecutter.main


@click.command()
@click.argument("url")
@click.option(
    "--interactive / --no-interactive",
    default=True,
    show_default=True,
    help="Prompt for template variables.",
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
@click.version_option()
def main(
    url: str,
    interactive: bool,
    checkout: Optional[str],
    output_dir: Optional[str],
) -> None:
    """cutty."""
    cutty.application.cookiecutter.main.main(
        url,
        interactive=interactive,
        checkout=checkout,
        output_dir=pathlib.Path(output_dir) if output_dir is not None else output_dir,
    )


if __name__ == "__main__":
    main(prog_name="cutty")  # pragma: no cover
