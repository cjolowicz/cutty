"""Fixtures for cutty.packages.domain.stores."""
import pathlib

import pytest
from yarl import URL

from cutty.packages.domain.registry import ProviderStore
from cutty.packages.domain.stores import Store


@pytest.fixture
def store(tmp_path: pathlib.Path) -> Store:
    """Fixture for a store."""
    path = tmp_path / "store"
    path.mkdir()

    def _(url: URL) -> pathlib.Path:
        return path

    return _


@pytest.fixture
def providerstore(store: Store) -> ProviderStore:
    """Fixture for a simple provider store."""

    def _(providername: str) -> Store:
        return store

    return _
