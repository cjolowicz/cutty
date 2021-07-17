"""Main entry-point for the command-line interface."""
import click


@click.group()
@click.version_option()
def main() -> None:
    """An experimental Cookiecutter clone."""
