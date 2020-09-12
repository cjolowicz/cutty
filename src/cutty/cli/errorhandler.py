"""Error handling."""
import sys
from typing import Iterator

from ..common.compat import contextmanager
from ..common.exceptions import CuttyException


@contextmanager
def errorhandler() -> Iterator[None]:
    """Print errors and exit with a status of 1."""
    try:
        yield
    except CuttyException as error:
        sys.exit(str(error))
