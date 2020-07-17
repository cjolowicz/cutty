"""Command-line interface."""
from typing import cast
from typing import Tuple

import click
from cookiecutter import cli

from .core import create


def validate_extra_context(
    context: click.Context, parameter: click.Parameter, value: Tuple[str]
) -> Tuple[str]:
    """Validate extra_context command-line argument.

    This is a simple wrapper used to simplify the return type.
    """
    result = cli.validate_extra_context(context, parameter, value)
    return cast(Tuple[str], () if result is None else result)


@click.command()
@click.argument("template")
@click.argument("extra_context", nargs=-1, callback=validate_extra_context)
def create(template: str, extra_context: Tuple[str]) -> None:
    """Create a project from a Cookiecutter template."""
    create(template, extra_context)
