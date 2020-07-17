"""Command-line interface."""
import click

from .core import create


@click.command()
@click.argument("template")
def create(template: str) -> None:
    """Create a project from a Cookiecutter template."""
    create(template)
