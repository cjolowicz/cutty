"""Fixtures for testing cutty.repositories."""
import pathlib

import pytest
from yarl import URL

from cutty.repositories.domain.providers import ProviderStore


@pytest.fixture
def url() -> URL:
    """Fixture for a URL."""
    return URL("https://example.com/repository")


@pytest.fixture
def providerstore(tmp_path: pathlib.Path) -> ProviderStore:
    """Fixture for a simple provider store."""
    path = tmp_path / "store"
    path.mkdir()
    return lambda providername: lambda url: path
