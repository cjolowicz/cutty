"""Fetcher for git repositories."""
import pathlib
from dataclasses import dataclass
from typing import NoReturn
from typing import Optional

import pygit2
from yarl import URL

from cutty.errors import CuttyError
from cutty.repositories.domain.fetchers import fetcher
from cutty.repositories.domain.matchers import scheme
from cutty.repositories.domain.revisions import Revision
from cutty.repositories.domain.stores import defaultstore
from cutty.util.exceptionhandlers import exceptionhandler
from cutty.util.git import Repository


@dataclass
class GitFetcherError(CuttyError):
    """Cannot access the remote repository."""

    message: str


@exceptionhandler
def _errorhandler(error: pygit2.GitError) -> NoReturn:
    raise GitFetcherError(str(error))


@fetcher(
    match=scheme("file", "git", "http", "https", "ssh"),
    store=lambda url: defaultstore(url).with_suffix(".git"),
)
@_errorhandler
def gitfetcher(
    url: URL, destination: pathlib.Path, revision: Optional[Revision]
) -> None:
    """Fetch a git repository."""
    if destination.exists():
        repository = Repository.open(destination)
        repository.fetch(prune=True)
    else:
        Repository.clone(str(url), destination, mirror=True)
