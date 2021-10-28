"""Unit tests for cutty.packages.domain.fetchers."""
from yarl import URL

from cutty.packages.domain.fetchers import Fetcher
from cutty.packages.domain.stores import Store
from tests.fixtures.packages.domain.types import FetcherCalls


pytest_plugins = [
    "tests.fixtures.packages.domain.fetchers",
    "tests.fixtures.packages.domain.stores",
]


def test_match(fakefetcher: Fetcher, url: URL, store: Store) -> None:
    """It delegates to the matcher."""
    assert not fakefetcher.match(url.with_scheme("http"))


def test_fetch_always(
    fakefetcher: Fetcher, fetchercalls: FetcherCalls, url: URL, store: Store
) -> None:
    """It delegates to the fetch function."""
    destination = store(url) / url.name
    path = fakefetcher.fetch(url, store)

    assert path == destination
    assert fetchercalls == [(url, destination)]
