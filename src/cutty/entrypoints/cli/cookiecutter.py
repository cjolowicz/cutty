"""Command-line interface for creating projects from Cookiecutter templates."""
import click

from cutty.entrypoints.cli._main import main as _main
from cutty.services.create import create as service_create


@_main.command()
@click.argument("template")
def cookiecutter(template: str) -> None:
    """Generate projects from Cookiecutter templates."""
    service_create(template)
