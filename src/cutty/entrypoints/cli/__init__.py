"""Command-line interface."""
from cutty.entrypoints.cli._main import main
from cutty.entrypoints.cli.cookiecutter import cookiecutter
from cutty.entrypoints.cli.create import create
from cutty.entrypoints.cli.update import update


registercommand = main.command()

registercommand(create)
registercommand(update)
registercommand(cookiecutter)


__all__ = ["main"]
