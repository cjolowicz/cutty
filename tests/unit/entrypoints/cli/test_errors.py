"""Unit tests for cutty.entrypoints.cli.errors."""
import pathlib

import pytest
from yarl import URL

from cutty.entrypoints.cli.errors import fatal
from cutty.errors import CuttyError
from cutty.repositories.adapters.fetchers.git import GitFetcherError
from cutty.repositories.domain.mounters import UnsupportedRevisionError
from cutty.repositories.domain.registry import UnknownLocationError


@pytest.mark.parametrize(
    "error",
    [
        GitFetcherError("unsupported URL protocol"),
        UnsupportedRevisionError("v1.0.0"),
        UnknownLocationError(URL("invalid://location")),
        UnknownLocationError(pathlib.Path("/no/such/file/or/directory")),
    ],
)
def test_errors(error: CuttyError) -> None:
    """It exits with an error message."""
    with pytest.raises(SystemExit, match="error: "):
        with fatal:
            raise error
