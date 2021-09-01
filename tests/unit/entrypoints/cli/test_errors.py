"""Unit tests for cutty.entrypoints.cli.errors."""
import pathlib

import pytest
from yarl import URL

from cutty.entrypoints.cli.errors import fatal
from cutty.errors import CuttyError
from cutty.repositories.domain.registry import UnknownLocationError


def test_fatal() -> None:
    """It raises SystemExit with the exception message."""
    with pytest.raises(SystemExit, match="error: Boom"):
        with fatal:
            raise CuttyError("Boom")


@pytest.mark.parametrize(
    "error",
    [
        UnknownLocationError(URL("invalid://location")),
        UnknownLocationError(pathlib.Path("/no/such/file/or/directory")),
    ],
)
def test_unknown_location_invalid_url(error: CuttyError) -> None:
    """It raises SystemExit instead of the original exception."""
    with pytest.raises(SystemExit):
        with fatal:
            raise error
