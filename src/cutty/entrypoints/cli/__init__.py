"""Command-line interface."""
from cutty.entrypoints.cli._main import main
from cutty.entrypoints.cli.cookiecutter import cookiecutter
from cutty.entrypoints.cli.create import create
from cutty.entrypoints.cli.errors import fatal
from cutty.entrypoints.cli.import_ import import_
from cutty.entrypoints.cli.link import link
from cutty.entrypoints.cli.update import update


registercommand = main.command()

for command in [create, update, link, cookiecutter]:
    registercommand(fatal(command))

main.command("import")(import_)

__all__ = ["main"]
