"""Command-line interface."""
from cutty.entrypoints.cli._main import main
from cutty.entrypoints.cli.cookiecutter import cookiecutter
from cutty.entrypoints.cli.create import create
from cutty.entrypoints.cli.errors import fatal
from cutty.entrypoints.cli.update import update


registercommand = main.command()

for command in [create, update, cookiecutter]:
    registercommand(fatal(command))


__all__ = ["main"]
