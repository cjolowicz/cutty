"""Fixtures for testing cutty.repositories2."""
import pathlib

import pytest
from yarl import URL

from cutty.repositories2.domain.providers import ProviderStore
from cutty.repositories2.domain.stores import Store


@pytest.fixture
def url() -> URL:
    """Fixture for a URL."""
    return URL("https://example.com/repository")


@pytest.fixture
def store(tmp_path: pathlib.Path) -> Store:
    """Fixture for a simple store."""
    path = tmp_path / "store"
    path.mkdir()
    return lambda url: path


@pytest.fixture
def providerstore(store: Store) -> ProviderStore:
    """Fixture for a simple provider store."""
    return lambda providername: store
