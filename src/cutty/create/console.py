"""Command-line interface."""
import json
import sys
from textwrap import dedent
from typing import Any
from typing import Iterator
from typing import Optional
from typing import Tuple

import click

from . import core
from .. import exceptions
from .. import git
from ..types import Context
from ..utils import as_optional_path


errors = (
    exceptions.FailedHookException,
    exceptions.InvalidModeException,
    exceptions.OutputDirExistsException,
    exceptions.UndefinedVariableInTemplate,
    exceptions.UnknownExtension,
    git.Error,
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


def format_error(error: Exception) -> str:
    """Return the error message for the exception."""
    if isinstance(error, exceptions.UndefinedVariableInTemplate):
        return format_undefined_variable_error(error)
    return str(error)


def validate_extra_context(*args: Any) -> Context:
    """Validate extra_context command-line argument."""
    try:  # pragma: no cover
        _, _, values = args
    except ValueError:
        # Typeguard confuses click < 8.0 because click inspects `__code__` to
        # determine the number of arguments to pass, and Typeguard's wrapper
        # has an argument count of zero due to the use of `*args`.
        _, values = args

    def _generate() -> Iterator[Tuple[str, str]]:
        for value in values:
            try:
                key, value = value.split("=", 1)
            except ValueError:
                raise click.BadParameter(
                    "EXTRA_CONTEXT should contain items of the form key=value; "
                    f"'{value}' doesn't match that form"
                )
            yield key, value

    return dict(_generate())


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("template")
@click.argument("extra_context", nargs=-1, callback=validate_extra_context)
@click.option(
    "--no-input",
    is_flag=True,
    help="Do not prompt for parameters and only use cookiecutter.json file content",
)
@click.option(
    "-c", "--checkout", help="branch, tag or commit to checkout after git clone"
)
@click.option(
    "--directory",
    help=(
        "Directory within repo that holds cookiecutter.json file "
        "for advanced repositories with multi templates in it"
    ),
)
@click.option(
    "--replay",
    is_flag=True,
    help="Do not prompt for parameters and only use information entered previously",
)
@click.option(
    "-f",
    "--overwrite-if-exists",
    is_flag=True,
    help="Overwrite the contents of the output directory if it already exists",
)
@click.option(
    "-s",
    "--skip-if-file-exists",
    is_flag=True,
    help="Skip the files in the corresponding directories if they already exist",
    default=False,
)
@click.option(
    "-o",
    "--output-dir",
    default=".",
    type=click.Path(),
    help="Where to output the generated project dir into",
)
@click.option(
    "--config-file",
    type=click.Path(),
    default=None,
    help="User configuration file",
    envvar="CUTTY_CONFIG",
)
@click.option(
    "--default-config",
    is_flag=True,
    help="Do not load a config file. Use the defaults instead",
)
def create(
    template: str,
    extra_context: Context,
    no_input: bool,
    checkout: Optional[str],
    directory: Optional[str],
    replay: bool,
    overwrite_if_exists: bool,
    skip_if_file_exists: bool,
    output_dir: str,
    config_file: Optional[str],
    default_config: bool,
) -> None:
    """Create a project from a Cookiecutter template."""
    try:
        core.create(
            template,
            extra_context,
            no_input=no_input,
            checkout=checkout,
            directory=as_optional_path(directory),
            replay=replay,
            overwrite_if_exists=overwrite_if_exists,
            skip_if_file_exists=skip_if_file_exists,
            output_dir=output_dir,
            config_file=as_optional_path(config_file),
            default_config=default_config,
        )
    except errors as error:
        message = format_error(error)
        sys.exit(message)
