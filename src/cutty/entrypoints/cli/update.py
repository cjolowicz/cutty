"""Command-line interface for updating projects from Cookiecutter templates."""
from cutty.entrypoints.cli._main import main as _main
from cutty.services.update import update as service_update


@_main.command()
def update() -> None:
    """Update a project with changes from its template."""
    service_update()
