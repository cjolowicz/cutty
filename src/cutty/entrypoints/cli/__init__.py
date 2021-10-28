"""Command-line interface."""
import click

from cutty.entrypoints.cli._main import main
from cutty.entrypoints.cli.cookiecutter import cookiecutter
from cutty.entrypoints.cli.create import create
from cutty.entrypoints.cli.errors import fatal
from cutty.entrypoints.cli.import_ import import_
from cutty.entrypoints.cli.link import link
from cutty.entrypoints.cli.update import update


for command in [create, update, link, cookiecutter]:
    command2 = click.command()(fatal(command))
    main.add_command(command2)

command2 = click.command("import")(import_)
main.add_command(command2)

__all__ = ["main"]
