"""Fixtures for cutty.repositories.domain.fetchers."""
import pathlib
from typing import Optional

import pytest
from yarl import URL

from cutty.repositories.domain.fetchers import Fetcher
from cutty.repositories.domain.fetchers import FetchMode
from cutty.repositories.domain.revisions import Revision
from cutty.repositories.domain.stores import Store


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
