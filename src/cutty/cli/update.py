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
def update(
    interactive: bool, revision: Optional[str], template_directory: Optional[str],
) -> None:
    """Update a project from a Cookiecutter template."""
    try:
        api.update(
            interactive=interactive,
            revision=revision,
            directory=as_optional_path(template_directory),
        )
    except git.Error as error:
        sys.exit(str(error))
