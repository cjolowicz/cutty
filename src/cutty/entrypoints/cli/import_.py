"""Command-line interface for importing changesets into projects."""
from pathlib import Path

import click

from cutty.entrypoints.cli.errors import fatal
from cutty.services.update import update


@click.command("import")
@fatal
def import_() -> None:
    """Import changesets from templates into projects."""
    update(
        Path.cwd(), extrabindings=(), interactive=True, revision=None, directory=None
    )
