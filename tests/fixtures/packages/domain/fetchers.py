"""Fixtures for cutty.packages.domain.fetchers."""
import pathlib

import pytest
from yarl import URL

from cutty.packages.domain.fetchers import Fetcher
from cutty.packages.domain.fetchers import fetcher
from cutty.packages.domain.matchers import scheme
from cutty.packages.domain.stores import Store
from tests.fixtures.packages.domain.types import FetcherCalls


@pytest.fixture
def nullfetcher() -> Fetcher:
    """Fixture for a fetcher that matches no URL."""

    class _Fetcher(Fetcher):
        def match(self, url: URL) -> bool:
            return False

        def fetch(self, url: URL, store: Store) -> pathlib.Path:
            raise NotImplementedError()

    return _Fetcher()


@pytest.fixture
def emptyfetcher() -> Fetcher:
    """Fixture for a fetcher that simply creates the destination path."""

    class _Fetcher(Fetcher):
        def match(self, url: URL) -> bool:
            return True

        def fetch(self, url: URL, store: Store) -> pathlib.Path:
            path = store(url) / url.name

            if path.suffix:
                path.touch()
            else:
                path.mkdir(exist_ok=True)

            return path

    return _Fetcher()


@pytest.fixture
def fetchercalls() -> FetcherCalls:
    """Fixture to record arguments in fetcher calls."""
    return []


@pytest.fixture
def fakefetcher(fetchercalls: FetcherCalls) -> Fetcher:
    """Fixture for a fetcher."""

    @fetcher(match=scheme("https"))
    def _(url: URL, destination: pathlib.Path) -> None:
        """Fake fetcher."""
        fetchercalls.append((url, destination))

    return _
