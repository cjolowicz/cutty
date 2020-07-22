"""Command-line interface."""
from typing import Optional

import click
from cookiecutter.log import configure_logger

from . import core
from ..create.console import validate_extra_context
from ..types import StrMapping


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("extra_context", nargs=-1, callback=validate_extra_context)
@click.option(
    "--interactive",
    is_flag=True,
    default=False,
    help="Prompt for parameters",
    show_default=True,
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
    "-v", "--verbose", is_flag=True, help="Print debug information", default=False
)
@click.option(
    "--config-file", type=click.Path(), default=None, help="User configuration file"
)
def update(
    extra_context: StrMapping,
    interactive: bool,
    checkout: Optional[str],
    directory: Optional[str],
    verbose: bool,
    config_file: Optional[str],
) -> None:
    """Update a project from a Cookiecutter template."""
    configure_logger(stream_level="DEBUG" if verbose else "INFO")
    core.update(
        extra_context,
        interactive=interactive,
        checkout=checkout,
        directory=directory,
        config_file=config_file,
    )
