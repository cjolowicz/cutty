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
def providerstore(tmp_path: pathlib.Path) -> ProviderStore:
    """Fixture for a simple provider store."""
    path = tmp_path / "providerstore"
    path.mkdir()

    def _providerstore(providername: str) -> Store:
        return lambda url: path

    return _providerstore


@pytest.fixture
def store(providerstore: ProviderStore) -> Store:
    """Fixture for a simple store."""
    return providerstore("default")
