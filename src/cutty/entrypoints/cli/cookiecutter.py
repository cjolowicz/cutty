"""Command-line interface for creating projects from Cookiecutter templates."""
import click

from cutty.entrypoints.cli._main import main as _main
from cutty.entrypoints.cli.create import extra_context_callback
from cutty.services.create import create as service_create


@_main.command()
@click.argument("template")
@click.argument("extra-context", nargs=-1, callback=extra_context_callback)
@click.option(
    "--no-input",
    is_flag=True,
    default=False,
    help="Do not prompt for template variables.",
)
def cookiecutter(template: str, extra_context: dict[str, str], no_input: bool) -> None:
    """Generate projects from Cookiecutter templates."""
    service_create(template, extra_context=extra_context, no_input=no_input)
