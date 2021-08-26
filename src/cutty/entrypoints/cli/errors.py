"""Error handling for the command-line interface."""
from typing import NoReturn

from cutty.errors import CuttyError
from cutty.repositories.domain.providers import UnknownLocationError
from cutty.util.exceptionhandlers import exceptionhandler


@exceptionhandler
def _unknownlocation(error: UnknownLocationError) -> NoReturn:
    raise SystemExit(f"fatal: {error}")


@exceptionhandler
def fatal(error: CuttyError) -> NoReturn:
    """Exit with an error message."""
    raise SystemExit(f"fatal: {error}")
