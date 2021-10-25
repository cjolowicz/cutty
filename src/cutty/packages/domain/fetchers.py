"""Fetching packages from URLs."""
import enum
import pathlib
from collections.abc import Callable
from typing import Optional
from typing import Protocol

from yarl import URL

from cutty.packages.domain.matchers import Matcher
from cutty.packages.domain.revisions import Revision
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
        revision: Optional[Revision] = None,
        mode: FetchMode = FetchMode.ALWAYS,
    ) -> Optional[pathlib.Path]:
        """Retrieve the package at the URL into local storage."""


FetchFunction = Callable[[URL, pathlib.Path, Optional[Revision]], None]
FetchDecorator = Callable[[FetchFunction], Fetcher]


def fetcher(*, match: Matcher, store: Store = defaultstore) -> FetchDecorator:
    """A fetcher retrieves a package from a URL into storage."""
    relativestore = store

    def _decorator(fetch: FetchFunction) -> Fetcher:
        def _fetcher(
            url: URL,
            store: Store,
            revision: Optional[Revision] = None,
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
                fetch(url, destination, revision)

            return destination

        return _fetcher

    return _decorator