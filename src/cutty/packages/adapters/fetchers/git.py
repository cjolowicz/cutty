"""Fetcher for git repositories."""
import pathlib
from dataclasses import dataclass
from typing import NoReturn

import pygit2
from yarl import URL

from cutty.errors import CuttyError
from cutty.packages.domain.fetchers import fetcher
from cutty.packages.domain.matchers import scheme
from cutty.packages.domain.stores import defaultstore
from cutty.util.exceptionhandlers import ExceptionHandler
from cutty.util.exceptionhandlers import exceptionhandler
from cutty.util.git import Repository


@dataclass
class GitFetcherError(CuttyError):
    """Cannot access the remote repository."""

    url: URL
    message: str


def _errorhandler(url: URL) -> ExceptionHandler:
    @exceptionhandler
    def _(error: pygit2.GitError) -> NoReturn:
        raise GitFetcherError(url, str(error))

    return _


@fetcher(
    match=scheme("file", "git", "http", "https", "ssh"),
    store=lambda url: defaultstore(url).with_suffix(".git"),
)
def gitfetcher(url: URL, destination: pathlib.Path) -> None:
    """Fetch a git repository."""
    with _errorhandler(url):
        if destination.exists():
            repository = Repository.open(destination)
            repository.fetch(prune=True)
        else:
            Repository.clone(str(url), destination, mirror=True)
