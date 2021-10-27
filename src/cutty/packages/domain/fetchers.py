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


def fetcher(*, match: Matcher, store: Store = defaultstore) -> FetchDecorator2:
    """A fetcher retrieves a package from a URL into storage."""
    relativestore = store

    def _decorator(fetch: FetchFunction) -> Fetcher:
        class _Fetcher(Fetcher):
            def match(self, url: URL) -> bool:
                return match(url)

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
