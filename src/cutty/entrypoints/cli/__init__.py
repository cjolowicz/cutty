"""Command-line interface."""
from cutty.entrypoints.cli._main import main as main
from cutty.entrypoints.cli.cookiecutter import cookiecutter
from cutty.entrypoints.cli.create import create
from cutty.entrypoints.cli.update import update


main.command()(create)
main.command()(update)
main.command()(cookiecutter)
