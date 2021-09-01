"""Unit tests for cutty.entrypoints.cli.errors."""
import pathlib

import pytest
from yarl import URL

from cutty.entrypoints.cli.errors import fatal
from cutty.errors import CuttyError
from cutty.repositories.domain.registry import UnknownLocationError


@pytest.mark.parametrize(
    "error",
    [
        UnknownLocationError(URL("invalid://location")),
        UnknownLocationError(pathlib.Path("/no/such/file/or/directory")),
    ],
)
def test_errors(error: CuttyError) -> None:
    """It exits with an error message."""
    with pytest.raises(SystemExit, match="error: "):
        with fatal:
            raise error
