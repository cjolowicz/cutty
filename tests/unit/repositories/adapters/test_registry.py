"""Unit tests for cutty.repositories.adapters.registry."""
from yarl import URL

from cutty.repositories.adapters.registry import defaultproviderregistry
from cutty.repositories.domain.fetchers import FetchMode
from cutty.repositories.domain.stores import Store


def test_defaultproviderregistry_non_empty() -> None:
    """It is not empty."""
    assert defaultproviderregistry


def test_defaultproviderregistry_strings() -> None:
    """Its keys are strings."""
    assert all(
        isinstance(providername, str) for providername in defaultproviderregistry
    )


def test_defaultproviderregistry_providerfactories(store: Store) -> None:
    """Its values are provider factories."""
    url = URL("mailto:you@example.com")
    for providerfactory in defaultproviderregistry.values():
        provider = providerfactory(store, FetchMode.ALWAYS)
        filesystem = provider(url, None)
        assert filesystem is None
