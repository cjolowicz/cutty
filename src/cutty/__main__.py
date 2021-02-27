"""Command-line interface."""
from pathlib import Path

import click

import cutty.application.cookiecutter.main


@click.command()
@click.argument("directory")
@click.version_option()
def main(directory: str) -> None:
    """cutty."""
    cutty.application.cookiecutter.main.main(Path(directory))


if __name__ == "__main__":
    main(prog_name="cutty")  # pragma: no cover
