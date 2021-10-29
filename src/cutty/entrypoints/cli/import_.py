"""Command-line interface for importing changesets into projects."""
from pathlib import Path
from typing import Optional

import click

from cutty.entrypoints.cli.errors import fatal
from cutty.services.update import update


@click.command("import")
@click.option(
    "--revision",
    metavar="REV",
    help="Branch, tag, or commit hash of the template repository.",
)
@fatal
def import_(revision: Optional[str]) -> None:
    """Import changesets from templates into projects."""
    update(
        Path.cwd(),
        extrabindings=(),
        interactive=True,
        revision=revision,
        directory=None,
    )
