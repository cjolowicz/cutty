"""Command-line interface."""
from typing import Tuple

import click
from cookiecutter.cli import validate_extra_context

from .core import create


@click.command()
@click.argument("template")
@click.argument("extra_context", nargs=-1, callback=validate_extra_context)
def create(template: str, extra_context: Tuple[str]) -> None:
    """Create a project from a Cookiecutter template."""
    create(template, extra_context)
