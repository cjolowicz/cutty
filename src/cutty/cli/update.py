"""Command-line interface for updating projects."""
import sys
from typing import Optional

import click

from ..api import update as api
from ..common import git
from ..common.utils import as_optional_path


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
    try:
        api.update(
            interactive=interactive,
            revision=revision,
            directory=as_optional_path(template_directory),
            config_file=as_optional_path(config),
        )
    except git.Error as error:
        sys.exit(str(error))
