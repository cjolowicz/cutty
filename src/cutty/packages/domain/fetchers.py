"""Fetching package repositories from URLs."""
import abc
import enum
import pathlib
from collections.abc import Callable
from typing import Optional
from typing import Protocol

from yarl import URL

from cutty.packages.domain.matchers import Matcher
from cutty.packages.domain.stores import defaultstore
from cutty.packages.domain.stores import Store


class FetchMode(enum.Enum):
    """Fetch mode."""

    ALWAYS = enum.auto()
    AUTO = enum.auto()
    NEVER = enum.auto()


class Fetcher(Protocol):
    """The typing protocol for a fetcher."""

    def __call__(
        self,
        url: URL,
        store: Store,
        mode: FetchMode = FetchMode.ALWAYS,
    ) -> Optional[pathlib.Path]:
        """Retrieve the package at the URL into local storage."""


class AbstractFetcher(abc.ABC):
    """A fetcher retrieves a package repository from a URL into storage."""

    @abc.abstractmethod
    def fetch(
        self,
        url: URL,
        store: Store,
        mode: FetchMode = FetchMode.ALWAYS,
    ) -> Optional[pathlib.Path]:
        """Retrieve the package repository at the URL into local storage."""


class Fetcher2(AbstractFetcher):
    """A fetcher retrieves a package repository from a URL into storage."""

    def __init__(self, fetcher: Fetcher):
        """Initialize."""
        self.fetcher = fetcher

    def fetch(
        self,
        url: URL,
        store: Store,
        mode: FetchMode = FetchMode.ALWAYS,
    ) -> Optional[pathlib.Path]:
        """Retrieve the package repository at the URL into local storage."""
        return self.fetcher(url, store, mode)


FetchFunction = Callable[[URL, pathlib.Path], None]
FetchDecorator = Callable[[FetchFunction], Fetcher]
FetchDecorator2 = Callable[[FetchFunction], AbstractFetcher]


def fetcher(*, match: Matcher, store: Store = defaultstore) -> FetchDecorator2:
    """A fetcher retrieves a package from a URL into storage."""
    relativestore = store

    def _decorator(fetch: FetchFunction) -> AbstractFetcher:
        class _Fetcher(AbstractFetcher):
            def fetch(
                self,
                url: URL,
                store: Store,
                mode: FetchMode = FetchMode.ALWAYS,
            ) -> Optional[pathlib.Path]:
                if not match(url):
                    return None

                destination = store(url) / relativestore(url)

                if (
                    mode is FetchMode.ALWAYS
                    or mode is FetchMode.AUTO
                    and not destination.exists()
                ):
                    fetch(url, destination)

                return destination

        return _Fetcher()

    return _decorator
