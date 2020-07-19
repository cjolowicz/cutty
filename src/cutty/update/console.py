"""Command-line interface."""
import click

from . import core


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
def update() -> None:
    """Update a project from a Cookiecutter template."""
    core.update()
