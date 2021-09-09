"""Unit tests for cutty.entrypoints.cli.errors."""
import pathlib

import httpx
import pytest
from yarl import URL

from cutty.entrypoints.cli.errors import fatal
from cutty.errors import CuttyError
from cutty.repositories.adapters.fetchers.file import FileFetcherError
from cutty.repositories.adapters.fetchers.git import GitFetcherError
from cutty.repositories.adapters.fetchers.http import HTTPFetcherError
from cutty.repositories.adapters.fetchers.mercurial import HgError
from cutty.repositories.adapters.fetchers.mercurial import HgNotFoundError
from cutty.repositories.adapters.providers.git import RevisionNotFoundError
from cutty.repositories.domain.mounters import UnsupportedRevisionError
from cutty.repositories.domain.registry import UnknownLocationError


@pytest.mark.parametrize(
    "error",
    [
        GitFetcherError(
            URL("ssh://git@github.com/user/repository.git"),
            "unsupported URL protocol",
        ),
        HgNotFoundError(),
        HgError(
            ("/usr/bin/hg", "pull"),
            "",
            "abort: no repository found in '/' (.hg not found)\n",
            255,
            None,
        ),
        HgError(("/usr/bin/hg",), "", "", 1, pathlib.Path("/home/user")),
        FileFetcherError(
            FileNotFoundError(2, "No such file or directory", "/no/such/file")
        ),
        HTTPFetcherError(
            httpx.TooManyRedirects(
                "Exceeded maximum allowed redirects.",
                request=httpx.Request("GET", "https://example.com/repository"),
            )
        ),
        RevisionNotFoundError("v1.0.0"),
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
