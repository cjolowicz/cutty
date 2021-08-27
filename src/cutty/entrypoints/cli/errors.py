"""Error handling for the command-line interface."""
from typing import NoReturn

from cutty.errors import CuttyError
from cutty.repositories.domain.registry import UnknownLocationError
from cutty.util.exceptionhandlers import exceptionhandler


@exceptionhandler
def _unknownlocation(error: UnknownLocationError) -> NoReturn:
    raise SystemExit(f"unknown location {error.location}")


@exceptionhandler
def _fatal(error: CuttyError) -> NoReturn:
    raise SystemExit(f"fatal: {error}")


fatal = _unknownlocation >> _fatal
