"""Fetch a repository via HTTP."""
from pathlib import Path
from typing import Optional

import httpx
from yarl import URL

from cutty.repositories.domain.fetchers import fetcher
from cutty.repositories.domain.matchers import scheme
from cutty.repositories.domain.revisions import Revision


@fetcher(match=scheme("http", "https"))
def httpfetcher(url: URL, destination: Path, revision: Optional[Revision]) -> None:
    """Fetch via HTTP."""
    with httpx.stream("GET", str(url)) as response:
        response.raise_for_status()

        with destination.open(mode="wb") as io:
            for data in response.iter_bytes():
                io.write(data)
