"""Command-line interface."""
import json
import sys
from textwrap import dedent
from typing import Any
from typing import cast
from typing import Tuple

import click
from cookiecutter import cli
from cookiecutter import exceptions
from cookiecutter.log import configure_logger

from . import core


errors = (
    exceptions.OutputDirExistsException,
    exceptions.FailedHookException,
    exceptions.UnknownExtension,
)


def format_undefined_variable_error(
    error: exceptions.UndefinedVariableInTemplate,
) -> str:
    """Provide some more detail when encountering undefined template variables."""
    context = json.dumps(error.context, indent=2, sort_keys=True)
    message = f"""\
    {error.message}
    Error message: {error.error.message}
    Context: {context}"""
    return dedent(message)


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
    configure_logger(stream_level="INFO")

    try:
        core.create(template, extra_context)
    except errors as error:
        sys.exit(str(error))
    except exceptions.UndefinedVariableInTemplate as error:
        message = format_undefined_variable_error(error)
        sys.exit(message)
