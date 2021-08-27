"""Unit tests for cutty.entrypoints.cli.errors."""
import pytest

from cutty.entrypoints.cli.errors import fatal
from cutty.errors import CuttyError


def test_fatal() -> None:
    """It raises SystemExit with the exception message."""
    with pytest.raises(SystemExit, match="fatal: Boom"):
        with fatal:
            raise CuttyError("Boom")
