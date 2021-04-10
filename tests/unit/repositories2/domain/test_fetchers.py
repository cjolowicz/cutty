"""Unit tests for cutty.repositories2.domain.fetchers."""
from pathlib import Path
from typing import Optional

import pytest
from yarl import URL

from cutty.repositories2.domain.fetchers import Fetcher
from cutty.repositories2.domain.fetchers import fetcher
from cutty.repositories2.domain.fetchers import FetchMode
from cutty.repositories2.domain.matchers import scheme
from cutty.repositories2.domain.stores import Store


@pytest.fixture
def store(tmp_path: Path) -> Store:
    """Fixture for a store."""
    return lambda url: tmp_path


@pytest.fixture
def fakefetcher() -> Fetcher:
    """Fixture for a fetcher."""

    @fetcher(match=scheme("https"))
    def fakefetcher(url: URL, destination: Path, revision: Optional[str]) -> None:
        """Fake fetcher."""
        fakefetcher.calls.append((url, destination, revision))

    fakefetcher.calls: list[tuple[URL, Path, Optional[str]]] = []

    return fakefetcher


@pytest.fixture
def url() -> URL:
    """Fixture with a URL."""
    return URL("https://example.com/repository")


def test_fetcher_match(fakefetcher: Fetcher, url: URL, store: Store) -> None:
    """It delegates to the matcher."""
    path = fakefetcher(
        url.with_scheme("http"), store, revision=None, mode=FetchMode.ALWAYS
    )
    assert path is None


def test_fetcher_fetch_always(fakefetcher: Fetcher, url: URL, store: Store) -> None:
    """It delegates to the fetch function."""
    destination = store(url) / url.name
    path = fakefetcher(url, store, revision=None, mode=FetchMode.ALWAYS)

    assert path == destination
    assert fakefetcher.calls == [(url, destination, None)]


def test_fetcher_fetch_never(fakefetcher: Fetcher, url: URL, store: Store) -> None:
    """It returns the destination without fetching."""
    destination = store(url) / url.name
    path = fakefetcher(url, store, revision=None, mode=FetchMode.NEVER)

    assert path == destination
    assert not fakefetcher.calls
