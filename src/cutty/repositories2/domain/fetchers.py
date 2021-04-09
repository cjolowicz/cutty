"""Fetching repositories from URLs."""
import abc
import enum
import pathlib
from collections.abc import Callable
from typing import Optional

from yarl import URL

from cutty.repositories2.domain.matchers import Matcher
from cutty.repositories2.domain.revisions import Revision
from cutty.repositories2.domain.stores import defaultstore
from cutty.repositories2.domain.stores import Store


class FetchMode(enum.Enum):
    """Fetch mode."""

    ALWAYS = enum.auto()
    AUTO = enum.auto()
    NEVER = enum.auto()


class Fetcher(abc.ABC):
    """A fetcher retrieves a repository from a URL into storage."""

    @abc.abstractmethod
    def match(self, url: URL) -> bool:
        """Return True if the fetcher supports the URL."""

    @abc.abstractmethod
    def fetch(
        self,
        url: URL,
        storage: pathlib.Path,
        revision: Optional[Revision] = None,
        mode: FetchMode = FetchMode.ALWAYS,
    ) -> pathlib.Path:
        """Fetch the repository from the URL."""


FetchFunction = Callable[[URL, pathlib.Path, Optional[Revision]], None]
FetchDecorator = Callable[[FetchFunction], Fetcher]


def fetcher(*, match: Matcher, store: Store = defaultstore) -> FetchDecorator:
    """Decorator for creating a fetcher."""

    def _decorator(fetch: FetchFunction) -> Fetcher:
        class _Fetcher(Fetcher):
            """A fetcher retrieves a repository from a URL into storage."""

            def match(self, url: URL) -> bool:
                """Return True if the fetcher supports the URL."""
                return match(url)

            def fetch(
                self,
                url: URL,
                storage: pathlib.Path,
                revision: Optional[Revision] = None,
                mode: FetchMode = FetchMode.ALWAYS,
            ) -> pathlib.Path:
                """Fetch the repository from the URL."""
                destination = storage / store(url)

                if (
                    mode is FetchMode.ALWAYS
                    or mode is FetchMode.AUTO
                    and not destination.exists()
                ):
                    fetch(url, destination, revision)

                return destination

        return _Fetcher()

    return _decorator
