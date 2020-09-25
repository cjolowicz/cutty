"""Command-line interface for creating projects."""
from typing import Optional

import click

from . import logging
from ..api import create as api
from ..core.utils import as_optional_path
from .errorhandler import errorhandler


@click.command()
@click.argument("template")
@click.option(
    "--interactive / --no-interactive",
    default=True,
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
    "-C",
    "--directory",
    metavar="DIR",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Parent directory of the generated project.",
)
@click.option(
    "--config",
    metavar="FILE",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, allow_dash=True),
    envvar="CUTTY_CONFIG",
    help="Configuration file.",
)
def create(
    template: str,
    interactive: bool,
    revision: Optional[str],
    template_directory: Optional[str],
    directory: Optional[str],
    config: Optional[str],
) -> None:
    """Create a project from a Cookiecutter template."""
    logging.configure()

    with errorhandler():
        api.create(
            template,
            interactive=interactive,
            revision=revision,
            directory=as_optional_path(template_directory),
            output_dir=as_optional_path(directory),
            config_file=as_optional_path(config),
        )
