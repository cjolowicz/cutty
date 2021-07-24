"""Command-line interface."""
# noreorder
from . import create  # noqa: F401
from . import update  # noqa: F401
from . import cookiecutter  # noqa: F401
from ._main import main as main  # noqa: F401

main.command()(create.create)
main.command()(update.update)
main.command()(cookiecutter.cookiecutter)
