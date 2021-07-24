"""Command-line interface."""
# noreorder
from . import create
from . import update
from . import cookiecutter
from ._main import main as main

main.command()(create.create)
main.command()(update.update)
main.command()(cookiecutter.cookiecutter)
