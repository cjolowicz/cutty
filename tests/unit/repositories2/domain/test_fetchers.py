"""Unit tests for cutty.repositories2.domain.fetchers."""
from pathlib import Path
from typing import Optional

import pytest
from yarl import URL

from cutty.repositories2.domain.fetchers import Fetcher
from cutty.repositories2.domain.fetchers import fetcher
from cutty.repositories2.domain.fetchers import FetchMode
from cutty.repositories2.domain.matchers import scheme


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


def test_fetcher_match(fakefetcher: Fetcher, url: URL) -> None:
    """It delegates to the matcher."""
    assert fakefetcher.match(url)


def test_fetcher_fetch_always(fakefetcher: Fetcher, url: URL, tmp_path: Path) -> None:
    """It delegates to the fetch function."""
    destination = tmp_path / url.name
    path = fakefetcher.fetch(url, destination.parent, None)

    assert path == destination
    assert fakefetcher.calls == [(url, destination, None)]


def test_fetcher_fetch_never(fakefetcher: Fetcher, url: URL, tmp_path: Path) -> None:
    """It returns the destination without fetching."""
    destination = tmp_path / url.name
    path = fakefetcher.fetch(url, destination.parent, None, FetchMode.NEVER)

    assert path == destination
    assert not fakefetcher.calls
