"""Fetch a repository from the filesystem."""
import pathlib
import shutil
from typing import Optional

from yarl import URL

from cutty.repositories.domain.fetchers import fetcher
from cutty.repositories.domain.locations import aspath
from cutty.repositories.domain.matchers import scheme
from cutty.repositories.domain.revisions import Revision


@fetcher(match=scheme("file"))
def filefetcher(
    url: URL, destination: pathlib.Path, revision: Optional[Revision]
) -> None:
    """Copy a file or directory."""
    if destination.is_dir():
        shutil.rmtree(destination)
    elif destination.exists():
        destination.unlink()

    source = aspath(url)

    if source.is_dir():
        shutil.copytree(source, destination, symlinks=True)
    else:
        shutil.copy2(source, destination, follow_symlinks=False)
