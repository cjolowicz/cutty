"""Command-line interface."""
from typing import Any
from typing import cast
from typing import Tuple

import click
from cookiecutter import cli

from . import core


def validate_extra_context(*args: Any) -> Tuple[str, ...]:
    """Validate extra_context command-line argument.

    This is a simple wrapper used to simplify the return type.
    """
    if len(args) != 3:  # pragma: no cover
        # Typeguard confuses click < 8.0 because click inspects `__code__` to
        # determine the number of arguments to pass, and Typeguard's wrapper
        # has an argument count of zero due to the use of `*args`.
        context, value = args
        args = (context, None, value)
    result = cli.validate_extra_context(*args)
    return cast(Tuple[str], () if result is None else result)


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("template")
@click.argument("extra_context", nargs=-1, callback=validate_extra_context)
def create(template: str, extra_context: Tuple[str, ...]) -> None:
    """Create a project from a Cookiecutter template."""
    core.create(template, extra_context)
