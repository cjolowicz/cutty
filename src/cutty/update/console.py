"""Command-line interface."""
from typing import Optional

import click

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
def update(
    extra_context: StrMapping, interactive: bool, checkout: Optional[str],
) -> None:
    """Update a project from a Cookiecutter template."""
    core.update(extra_context, interactive=interactive, checkout=checkout)
