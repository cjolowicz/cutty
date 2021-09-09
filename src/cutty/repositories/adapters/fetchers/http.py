"""Fetch a repository via HTTP."""
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn
from typing import Optional

import httpx
from yarl import URL

from cutty.errors import CuttyError
from cutty.repositories.domain.fetchers import fetcher
from cutty.repositories.domain.matchers import scheme
from cutty.repositories.domain.revisions import Revision
from cutty.util.exceptionhandlers import exceptionhandler


@dataclass
class HTTPFetcherError(CuttyError):
    """The HTTP resource could not be fetched."""

    error: httpx.HTTPError


@exceptionhandler
def _errorhandler(error: httpx.HTTPError) -> NoReturn:
    raise HTTPFetcherError(error)


@fetcher(match=scheme("http", "https"))
@_errorhandler
def httpfetcher(url: URL, destination: Path, revision: Optional[Revision]) -> None:
    """Fetch via HTTP."""
    with httpx.stream("GET", str(url)) as response:
        response.raise_for_status()

        with destination.open(mode="wb") as io:
            for data in response.iter_bytes():
                io.write(data)
