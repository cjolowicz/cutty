"""Fetching package repositories from URLs."""
import abc
import pathlib
from collections.abc import Callable

from yarl import URL

from cutty.packages.domain.matchers import Matcher
from cutty.packages.domain.stores import defaultstore
from cutty.packages.domain.stores import Store


class Fetcher(abc.ABC):
    """A fetcher retrieves a package repository from a URL into storage."""

    @abc.abstractmethod
    def match(self, url: URL) -> bool:
        """Return True if the fetcher can handle the URL."""

    @abc.abstractmethod
    def fetch(self, url: URL, store: Store) -> pathlib.Path:
        """Retrieve the package repository at the URL into local storage."""


FetchFunction = Callable[[URL, pathlib.Path], None]
FetchDecorator = Callable[[FetchFunction], Fetcher]


class _Fetcher(Fetcher):
    def __init__(self, fetch: FetchFunction, *, match: Matcher, store: Store) -> None:
        self._fetch = fetch
        self._match = match
        self._store = store

    def match(self, url: URL) -> bool:
        return self._match(url)

    def fetch(self, url: URL, store: Store) -> pathlib.Path:
        destination = store(url) / self._store(url)

        self._fetch(url, destination)

        return destination


def fetcher(*, match: Matcher, store: Store = defaultstore) -> FetchDecorator:
    """A fetcher retrieves a package from a URL into storage."""

    def _decorator(fetch: FetchFunction) -> Fetcher:
        return _Fetcher(fetch, match=match, store=store)

    return _decorator
