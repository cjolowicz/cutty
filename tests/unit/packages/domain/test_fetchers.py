"""Unit tests for cutty.packages.domain.fetchers."""
from yarl import URL

from cutty.packages.domain.fetchers import AbstractFetcher
from cutty.packages.domain.fetchers import FetchMode
from cutty.packages.domain.stores import Store
from tests.fixtures.packages.domain.types import FetcherCalls


pytest_plugins = [
    "tests.fixtures.packages.domain.fetchers",
    "tests.fixtures.packages.domain.stores",
]


def test_match(fakefetcher: AbstractFetcher, url: URL, store: Store) -> None:
    """It delegates to the matcher."""
    path = fakefetcher.fetch(url.with_scheme("http"), store)
    assert path is None


def test_fetch_always(
    fakefetcher: AbstractFetcher, fetchercalls: FetcherCalls, url: URL, store: Store
) -> None:
    """It delegates to the fetch function."""
    destination = store(url) / url.name
    path = fakefetcher.fetch(url, store)

    assert path == destination
    assert fetchercalls == [(url, destination)]


def test_fetch_never(
    fakefetcher: AbstractFetcher, fetchercalls: FetcherCalls, url: URL, store: Store
) -> None:
    """It returns the destination without fetching."""
    destination = store(url) / url.name
    path = fakefetcher.fetch(url, store, FetchMode.NEVER)

    assert path == destination
    assert not fetchercalls
