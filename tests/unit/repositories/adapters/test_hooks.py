"""Unit tests for cutty.repositories.adapters.hooks."""
import pytest
from yarl import URL

from cutty.plugins.adapters.fake import FakeRegistry
from cutty.repositories.adapters.hooks import getproviderstore
from cutty.repositories.adapters.hooks import getrepositoryprovider


def test_getrepositorystorage() -> None:
    """It is idempotent."""
    url = URL("https://example.com/repository.git")
    registry = FakeRegistry()
    providerstore = getproviderstore(registry, "cutty")
    store = providerstore("git")
    assert store(url) == store(url)


def test_getrepositoryprovider() -> None:
    """It raises an exception for an invalid scheme."""
    registry = FakeRegistry()
    repositoryprovider = getrepositoryprovider(registry, "cutty")
    with pytest.raises(Exception):
        repositoryprovider("invalid-scheme://example.com/repository")
