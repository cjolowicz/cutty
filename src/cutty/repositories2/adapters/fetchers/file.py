"""Fetch a repository from the filesystem."""
import pathlib
import shutil
from typing import Optional

from yarl import URL

from cutty.repositories2.domain.fetchers import fetcher
from cutty.repositories2.domain.matchers import scheme
from cutty.repositories2.domain.revisions import Revision
from cutty.repositories2.domain.urls import aspath


@fetcher(match=scheme("file"))
def filefetcher(
    url: URL, destination: pathlib.Path, revision: Optional[Revision]
) -> None:
    """Copy a file."""
    if destination.exists():
        shutil.rmtree(destination)

    source = aspath(url)
    shutil.copytree(source, destination, symlinks=True)
