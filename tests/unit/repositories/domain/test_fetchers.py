"""Unit tests for cutty.repositories.domain.fetchers."""
from pathlib import Path
from typing import Optional

import pytest
from yarl import URL

from cutty.repositories.domain.fetchers import Fetcher
from cutty.repositories.domain.fetchers import fetcher
from cutty.repositories.domain.fetchers import FetchMode
from cutty.repositories.domain.matchers import scheme
from cutty.repositories.domain.stores import Store


@pytest.fixture
def store(tmp_path: Path) -> Store:
    """Fixture for a store."""
    return lambda url: tmp_path


FetcherCalls = list[tuple[URL, Path, Optional[str]]]


@pytest.fixture
def fetchercalls() -> FetcherCalls:
    """Fixture to record arguments in fetcher calls."""
    return []


@pytest.fixture
def fakefetcher(fetchercalls: FetcherCalls) -> Fetcher:
    """Fixture for a fetcher."""

    @fetcher(match=scheme("https"))
    def fakefetcher(url: URL, destination: Path, revision: Optional[str]) -> None:
        """Fake fetcher."""
        fetchercalls.append((url, destination, revision))

    return fakefetcher


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
