"""Fixtures for cutty.packages.domain.fetchers."""
import pathlib
from typing import Optional

import pytest
from yarl import URL

from cutty.packages.domain.fetchers import AbstractFetcher
from cutty.packages.domain.fetchers import fetcher
from cutty.packages.domain.fetchers import Fetcher2
from cutty.packages.domain.fetchers import FetchMode
from cutty.packages.domain.matchers import scheme
from cutty.packages.domain.stores import Store
from tests.fixtures.packages.domain.types import FetcherCalls


@pytest.fixture
def nullfetcher() -> AbstractFetcher:
    """Fixture for a fetcher that matches no URL."""

    class _Fetcher(AbstractFetcher):
        def fetch(
            self,
            url: URL,
            store: Store,
            mode: FetchMode = FetchMode.ALWAYS,
        ) -> Optional[pathlib.Path]:
            return None

    return _Fetcher()


@pytest.fixture
def emptyfetcher() -> AbstractFetcher:
    """Fixture for a fetcher that simply creates the destination path."""

    def _(
        url: URL, store: Store, mode: FetchMode = FetchMode.ALWAYS
    ) -> Optional[pathlib.Path]:
        path = store(url) / url.name

        if path.suffix:
            path.touch()
        else:
            path.mkdir(exist_ok=True)

        return path

    return Fetcher2(_)


@pytest.fixture
def fetchercalls() -> FetcherCalls:
    """Fixture to record arguments in fetcher calls."""
    return []


@pytest.fixture
def fakefetcher(fetchercalls: FetcherCalls) -> AbstractFetcher:
    """Fixture for a fetcher."""

    @fetcher(match=scheme("https"))
    def _(url: URL, destination: pathlib.Path) -> None:
        """Fake fetcher."""
        fetchercalls.append((url, destination))

    return _
