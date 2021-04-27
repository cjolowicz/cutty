"""Unit tests for cutty.repositories.adapters.hooks."""
from yarl import URL

from cutty.plugins.adapters.fake import FakeRegistry
from cutty.repositories.adapters.hooks import getproviderstore


def test_getrepositorystorage() -> None:
    """It is idempotent."""
    url = URL("https://example.com/repository.git")
    registry = FakeRegistry()
    providerstore = getproviderstore(registry, "cutty")
    store = providerstore("git")
    assert store(url) == store(url)
