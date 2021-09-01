"""Error handling for the command-line interface."""
import pathlib
from typing import NoReturn

from cutty.errors import CuttyError
from cutty.repositories.domain.registry import UnknownLocationError
from cutty.util.exceptionhandlers import exceptionhandler


def _die(message: str) -> NoReturn:
    raise SystemExit(f"error: {message}")


@exceptionhandler
def _unknownlocation(error: UnknownLocationError) -> NoReturn:
    if isinstance(error.location, pathlib.Path) and not error.location.exists():
        _die(f"no such file or directory: {error.location}")

    _die(f"unknown location {error.location}")


@exceptionhandler
def _fatal(error: CuttyError) -> NoReturn:
    _die(str(error))


fatal = _unknownlocation >> _fatal
