"""Command-line interface."""
import click

from .legacy.create.console import create
from .legacy.update.console import update


@click.group()
@click.version_option(None, "-V", "--version")
def main() -> None:
    """Cutty."""


main.add_command(create)
main.add_command(update)


if __name__ == "__main__":
    main(prog_name="cutty")  # pragma: no cover
