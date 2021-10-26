"""Fetch a package via HTTP."""
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn

import httpx
from yarl import URL

from cutty.errors import CuttyError
from cutty.packages.domain.fetchers import fetcher
from cutty.packages.domain.matchers import scheme
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
def httpfetcher(url: URL, destination: Path) -> None:
    """Fetch via HTTP."""
    with httpx.stream("GET", str(url)) as response:
        response.raise_for_status()

        with destination.open(mode="wb") as io:
            for data in response.iter_bytes():
                io.write(data)
