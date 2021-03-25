"""Command-line interface."""
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
    "--revision",
    metavar="REV",
    help="Branch, tag, or commit hash of the template repository.",
)
@click.version_option()
def main(url: str, interactive: bool, revision: Optional[str]) -> None:
    """cutty."""
    cutty.application.cookiecutter.main.main(
        url, interactive=interactive, revision=revision
    )


if __name__ == "__main__":
    main(prog_name="cutty")  # pragma: no cover
