"""Fetching package repositories from URLs."""
import abc
import enum
import pathlib
from collections.abc import Callable
from typing import Optional

from yarl import URL

from cutty.packages.domain.matchers import Matcher
from cutty.packages.domain.stores import defaultstore
from cutty.packages.domain.stores import Store


class FetchMode(enum.Enum):
    """Fetch mode."""

    ALWAYS = enum.auto()
    AUTO = enum.auto()
    NEVER = enum.auto()


class Fetcher(abc.ABC):
    """A fetcher retrieves a package repository from a URL into storage."""

    @abc.abstractmethod
    def fetch(
        self,
        url: URL,
        store: Store,
        mode: FetchMode = FetchMode.ALWAYS,
    ) -> Optional[pathlib.Path]:
        """Retrieve the package repository at the URL into local storage."""


FetchFunction = Callable[[URL, pathlib.Path], None]
FetchDecorator2 = Callable[[FetchFunction], Fetcher]


class _Fetcher(Fetcher):
    def __init__(self, fetch: FetchFunction, *, match: Matcher, store: Store) -> None:
        self._fetch = fetch
        self._match = match
        self._store = store

    def match(self, url: URL) -> bool:
        return self._match(url)

    def fetch(
        self,
        url: URL,
        store: Store,
        mode: FetchMode = FetchMode.ALWAYS,
    ) -> Optional[pathlib.Path]:
        if not self.match(url):
            return None

        return self.fetch2(url, store, mode)

    def fetch2(
        self,
        url: URL,
        store: Store,
        mode: FetchMode = FetchMode.ALWAYS,
    ) -> pathlib.Path:
        destination = store(url) / self._store(url)

        if (
            mode is FetchMode.ALWAYS
            or mode is FetchMode.AUTO
            and not destination.exists()
        ):
            self._fetch(url, destination)

        return destination


def fetcher(*, match: Matcher, store: Store = defaultstore) -> FetchDecorator2:
    """A fetcher retrieves a package from a URL into storage."""

    def _decorator(fetch: FetchFunction) -> Fetcher:
        return _Fetcher(fetch, match=match, store=store)

    return _decorator
