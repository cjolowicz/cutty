"""Main entry point of the command-line interface."""
import click

from .create import create
from .update import update


@click.group()
@click.version_option()
def main() -> None:
    """Cutty creates projects from templates."""


main.add_command(create)
main.add_command(update)
