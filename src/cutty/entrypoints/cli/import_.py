"""Command-line interface for importing changesets into projects."""
import click

from cutty.entrypoints.cli.errors import fatal


@click.command("import")
@fatal
def import_() -> None:
    """Import changesets from templates into projects."""
