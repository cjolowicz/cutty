"""Command-line interface for updating projects from Cookiecutter templates."""
import click

from cutty.entrypoints.cli._main import main as _main
from cutty.entrypoints.cli.create import extra_context_callback
from cutty.services.update import update as service_update


@_main.command()
@click.argument("extra-context", nargs=-1, callback=extra_context_callback)
def update(extra_context: dict[str, str]) -> None:
    """Update a project with changes from its template."""
    service_update()
