"""Command-line interface for updating projects."""
from typing import Optional

import click

from ..api import update as api
from ..common.utils import as_optional_path
from .errorhandler import errorhandler


@click.command()
@click.option(
    "--interactive / --no-interactive",
    default=False,
    show_default=True,
    help="Prompt for template variables.",
)
@click.option(
    "--revision",
    metavar="REV",
    help="Branch, tag, or commit hash of the template repository.",
)
@click.option(
    "--template-directory",
    metavar="DIR",
    help=(
        "Directory within the template repository that contains the "
        "cookiecutter.json file."
    ),
)
@click.option(
    "--config",
    metavar="FILE",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, allow_dash=True),
    envvar="CUTTY_CONFIG",
    help="Configuration file.",
)
def update(
    interactive: bool,
    revision: Optional[str],
    template_directory: Optional[str],
    config: Optional[str],
) -> None:
    """Update a project from a Cookiecutter template."""
    with errorhandler():
        api.update(
            interactive=interactive,
            revision=revision,
            directory=as_optional_path(template_directory),
            config_file=as_optional_path(config),
        )
