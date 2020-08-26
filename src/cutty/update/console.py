"""Command-line interface."""
from typing import Optional

import click

from . import core
from ..utils import as_optional_path


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
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
def update(
    interactive: bool,
    checkout: Optional[str],
    directory: Optional[str],
    config_file: Optional[str],
    default_config: bool,
) -> None:
    """Update a project from a Cookiecutter template."""
    core.update(
        interactive=interactive,
        checkout=checkout,
        directory=as_optional_path(directory),
        config_file=as_optional_path(config_file),
        default_config=default_config,
    )
