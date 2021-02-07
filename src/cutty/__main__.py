"""Command-line interface."""
import click


@click.command()
@click.version_option()
def main() -> None:
    """cutty."""


if __name__ == "__main__":
    main(prog_name="cutty")  # pragma: no cover
