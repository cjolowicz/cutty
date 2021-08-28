"""Fixtures for cutty.repositories.domain.fetchers."""
import pathlib
from typing import Optional

import pytest
from yarl import URL

from cutty.repositories.domain.fetchers import Fetcher
from cutty.repositories.domain.fetchers import fetcher
from cutty.repositories.domain.fetchers import FetchMode
from cutty.repositories.domain.matchers import scheme
from cutty.repositories.domain.revisions import Revision
from cutty.repositories.domain.stores import Store


FetcherCalls = list[tuple[URL, pathlib.Path, Optional[str]]]


@pytest.fixture
def fetchercalls() -> FetcherCalls:
    """Fixture to record arguments in fetcher calls."""
    return []


@pytest.fixture
def fakefetcher(fetchercalls: FetcherCalls) -> Fetcher:
    """Fixture for a fetcher."""

    @fetcher(match=scheme("https"))
    def fakefetcher(
        url: URL, destination: pathlib.Path, revision: Optional[str]
    ) -> None:
        """Fake fetcher."""
        fetchercalls.append((url, destination, revision))

    return fakefetcher


@pytest.fixture
def emptyfetcher() -> Fetcher:
    """Fixture for a fetcher that simply creates the destination path."""

    def _fetcher(
        url: URL, store: Store, revision: Optional[Revision], mode: FetchMode
    ) -> Optional[pathlib.Path]:
        path = store(url) / url.name

        if path.suffix:
            path.touch()
        else:
            path.mkdir(exist_ok=True)

        return path

    return _fetcher


@pytest.fixture
def nullfetcher() -> Fetcher:
    """Fixture for a fetcher that matches no URL."""

    def _(
        url: URL, store: Store, revision: Optional[Revision], mode: FetchMode
    ) -> Optional[pathlib.Path]:
        return None

    return _
