"""Command-line interface for creating projects from Cookiecutter templates."""
import click

from cutty.entrypoints.cli._main import main as _main
from cutty.services.create import create as service_create


@_main.command()
@click.argument("template")
@click.option(
    "--no-input",
    is_flag=True,
    default=False,
    help="Do not prompt for template variables.",
)
def cookiecutter(template: str, no_input: bool) -> None:
    """Generate projects from Cookiecutter templates."""
    service_create(template, no_input=no_input)
