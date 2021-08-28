"""Unit tests for cutty.repositories.domain.fetchers."""
from pathlib import Path

import pytest
from yarl import URL

from cutty.repositories.domain.fetchers import Fetcher
from cutty.repositories.domain.fetchers import FetchMode
from cutty.repositories.domain.stores import Store
from tests.fixtures.repositories.domain.fetchers import FetcherCalls


pytest_plugins = ["tests.fixtures.repositories.domain.fetchers"]


@pytest.fixture
def store(tmp_path: Path) -> Store:
    """Fixture for a store."""
    return lambda url: tmp_path


def test_fetcher_match(fakefetcher: Fetcher, url: URL, store: Store) -> None:
    """It delegates to the matcher."""
    path = fakefetcher(url.with_scheme("http"), store, None, FetchMode.ALWAYS)
    assert path is None


def test_fetcher_fetch_always(
    fakefetcher: Fetcher, fetchercalls: FetcherCalls, url: URL, store: Store
) -> None:
    """It delegates to the fetch function."""
    destination = store(url) / url.name
    path = fakefetcher(url, store, None, FetchMode.ALWAYS)

    assert path == destination
    assert fetchercalls == [(url, destination, None)]


def test_fetcher_fetch_never(
    fakefetcher: Fetcher, fetchercalls: FetcherCalls, url: URL, store: Store
) -> None:
    """It returns the destination without fetching."""
    destination = store(url) / url.name
    path = fakefetcher(url, store, None, FetchMode.NEVER)

    assert path == destination
    assert not fetchercalls
