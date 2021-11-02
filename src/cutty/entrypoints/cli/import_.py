"""Command-line interface for importing changesets into projects."""
from pathlib import Path
from typing import Optional

import click

from cutty.entrypoints.cli.cookiecutter import extra_context_callback
from cutty.entrypoints.cli.errors import fatal
from cutty.services.import_ import import_ as service
from cutty.templates.domain.bindings import Binding


@click.command("import")
@click.option(
    "--revision",
    metavar="REV",
    help="Branch, tag, or commit hash of the template repository.",
)
@click.argument("extra-context", nargs=-1, callback=extra_context_callback)
@fatal
def import_(revision: Optional[str], extra_context: dict[str, str]) -> None:
    """Import changesets from templates into projects."""
    extrabindings = [Binding(key, value) for key, value in extra_context.items()]

    service(Path.cwd(), revision=revision, extrabindings=extrabindings)
