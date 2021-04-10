"""Fetch a repository via FTP."""
import pathlib
import shutil
import urllib.request
from typing import Optional

from yarl import URL

from cutty.repositories2.domain.fetchers import fetcher
from cutty.repositories2.domain.matchers import scheme
from cutty.repositories2.domain.revisions import Revision


@fetcher(match=scheme("ftp"))
def ftpfetcher(
    url: URL, destination: pathlib.Path, revision: Optional[Revision]
) -> None:
    """Fetch via FTP."""
    with urllib.request.urlopen(str(url)) as response:  # noqa: S310
        status: int = response.status  # type: ignore[attr-defined]
        if 400 <= status <= 599:
            raise RuntimeError(f"fetch failed: {url}: {status}")
        with destination.open(mode="wb") as io:
            shutil.copyfileobj(response, io)  # type: ignore[arg-type]
