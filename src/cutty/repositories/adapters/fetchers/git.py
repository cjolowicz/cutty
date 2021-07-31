"""Fetcher for git repositories."""
import pathlib
from typing import Optional

from yarl import URL

from cutty.repositories.domain.fetchers import fetcher
from cutty.repositories.domain.matchers import scheme
from cutty.repositories.domain.revisions import Revision
from cutty.repositories.domain.stores import defaultstore
from cutty.util.git import Repository


@fetcher(
    match=scheme("file", "ftp", "ftps", "git", "http", "https", "ssh"),
    store=lambda url: defaultstore(url).with_suffix(".git"),
)
def gitfetcher(
    url: URL, destination: pathlib.Path, revision: Optional[Revision]
) -> None:
    """Fetch a git repository."""
    if destination.exists():
        repository = Repository.open(destination)
        repository.fetch(prune=True)
    else:
        Repository.clone(str(url), destination, mirror=True)
