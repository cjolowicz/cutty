"""Fetch a repository via FTP."""
import pathlib
import shutil
import urllib.request
from typing import Optional

from yarl import URL

from cutty.repositories.domain.fetchers import fetcher
from cutty.repositories.domain.matchers import scheme
from cutty.repositories.domain.revisions import Revision


@fetcher(match=scheme("ftp"))
def ftpfetcher(
    url: URL, destination: pathlib.Path, revision: Optional[Revision]
) -> None:
    """Fetch via FTP."""
    # URLs with IPv6 literals are not supported, because
    # urllib.request.FTPHandler uses socket.gethostbyname.

    with urllib.request.urlopen(str(url)) as response:  # noqa: S310

        # FTPHandler does not set response.status, so we don't check it. Any
        # errors are raised as urllib.error.URLError.

        with destination.open(mode="wb") as io:
            shutil.copyfileobj(response, io)
