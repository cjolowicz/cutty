"""Error handling."""
import sys
from typing import Iterator

from rich.console import Console

from ..core.compat import contextmanager
from ..core.exceptions import CuttyException


@contextmanager
def errorhandler() -> Iterator[None]:
    """Print errors and exit with a status of 1."""
    try:
        yield
    except CuttyException as error:
        sys.exit(str(error))
    except Exception:
        Console().print_exception()
