"""Command-line interface."""
from cutty.entrypoints.cli._main import main
from cutty.entrypoints.cli.cookiecutter import cookiecutter
from cutty.entrypoints.cli.create import create
from cutty.entrypoints.cli.import_ import import_
from cutty.entrypoints.cli.link import link
from cutty.entrypoints.cli.update import update


for command in [create, update, link, cookiecutter, import_]:
    main.add_command(command)

__all__ = ["main"]
