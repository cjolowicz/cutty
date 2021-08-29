"""Fixtures for testing cutty.repositories."""
import pytest
from yarl import URL


@pytest.fixture
def url() -> URL:
    """Fixture for a URL."""
    return URL("https://example.com/repository")
