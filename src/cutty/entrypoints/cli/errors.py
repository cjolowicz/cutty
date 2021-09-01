"""Error handling for the command-line interface."""
import pathlib
from typing import NoReturn

from cutty.errors import CuttyError
from cutty.repositories.domain.registry import UnknownLocationError
from cutty.util.exceptionhandlers import exceptionhandler


@exceptionhandler
def _unknownlocation(error: UnknownLocationError) -> NoReturn:
    if isinstance(error.location, pathlib.Path) and not error.location.exists():
        raise SystemExit(f"error: no such file or directory: {error.location}")

    raise SystemExit(f"error: unknown location {error.location}")


@exceptionhandler
def _fatal(error: CuttyError) -> NoReturn:
    raise SystemExit(f"error: {error}")


fatal = _unknownlocation >> _fatal
