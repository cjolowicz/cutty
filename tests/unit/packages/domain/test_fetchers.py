"""Unit tests for cutty.packages.domain.fetchers."""
from yarl import URL

from cutty.packages.domain.fetchers import Fetcher
from cutty.packages.domain.fetchers import FetchMode
from cutty.packages.domain.stores import Store
from tests.fixtures.repositories.domain.types import FetcherCalls


pytest_plugins = [
    "tests.fixtures.repositories.domain.fetchers",
    "tests.fixtures.repositories.domain.stores",
]


def test_match(fakefetcher: Fetcher, url: URL, store: Store) -> None:
    """It delegates to the matcher."""
    path = fakefetcher(url.with_scheme("http"), store)
    assert path is None


def test_fetch_always(
    fakefetcher: Fetcher, fetchercalls: FetcherCalls, url: URL, store: Store
) -> None:
    """It delegates to the fetch function."""
    destination = store(url) / url.name
    path = fakefetcher(url, store)

    assert path == destination
    assert fetchercalls == [(url, destination, None)]


def test_fetch_never(
    fakefetcher: Fetcher, fetchercalls: FetcherCalls, url: URL, store: Store
) -> None:
    """It returns the destination without fetching."""
    destination = store(url) / url.name
    path = fakefetcher(url, store, None, FetchMode.NEVER)

    assert path == destination
    assert not fetchercalls
