"""Command-line interface for creating projects from Cookiecutter templates."""
from cutty.entrypoints.cli._main import main as _main


@_main.command()
def cookiecutter() -> None:
    """Generate projects from Cookiecutter templates."""
