"""Unit tests for cutty.entrypoints.cli.errors."""
import pathlib

import httpx
import pytest
from yarl import URL

from cutty.entrypoints.cli.errors import fatal
from cutty.errors import CuttyError
from cutty.packages.adapters.fetchers.file import FileFetcherError
from cutty.packages.adapters.fetchers.git import GitFetcherError
from cutty.packages.adapters.fetchers.http import HTTPFetcherError
from cutty.packages.adapters.fetchers.mercurial import HgError
from cutty.packages.adapters.fetchers.mercurial import HgNotFoundError
from cutty.packages.adapters.providers.git import RevisionNotFoundError
from cutty.packages.domain.mounters import UnsupportedRevisionError
from cutty.packages.domain.registry import UnknownLocationError
from cutty.projects.repository import NoUpdateInProgressError
from cutty.services.link import TemplateNotSpecifiedError
from cutty.util.git import MergeConflictError


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
        HgError(
            ("/usr/bin/hg", "update", "--rev", "invalid"),
            "",
            "abort: unknown revision 'invalid'\n",
            255,
            pathlib.Path("/home/user/repository"),
        ),
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
        TemplateNotSpecifiedError(),
        NoUpdateInProgressError(),
        MergeConflictError({"README.md"}),
    ],
)
def test_errors(error: CuttyError) -> None:
    """It exits with an error message."""
    with pytest.raises(SystemExit, match="error: "):
        with fatal:
            raise error
