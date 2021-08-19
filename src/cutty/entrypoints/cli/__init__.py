"""Command-line interface."""
from cutty.entrypoints.cli._main import main
from cutty.entrypoints.cli.cookiecutter import cookiecutter
from cutty.entrypoints.cli.create import create
from cutty.entrypoints.cli.errors import fatal
from cutty.entrypoints.cli.update import update


registercommand = main.command()

registercommand(fatal(create))
registercommand(fatal(update))
registercommand(fatal(cookiecutter))


__all__ = ["main"]
