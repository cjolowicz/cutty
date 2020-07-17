"""Command-line interface."""
import click

from .create.console import create


@click.group()
@click.version_option()
def main() -> None:
    """Cutty."""


main.add_command(create)


if __name__ == "__main__":
    main(prog_name="cutty")  # pragma: no cover
