"""Command-line interface."""
import click


@click.command()
@click.version_option()
def main() -> None:
    """Cutty."""


if __name__ == "__main__":
    main(prog_name="cutty")  # pragma: no cover
