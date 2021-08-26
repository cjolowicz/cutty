"""Unit tests for cutty.repositories.adapters.registry."""
from yarl import URL

from cutty.repositories.adapters.registry import defaultproviderfactories
from cutty.repositories.domain.fetchers import FetchMode
from cutty.repositories.domain.stores import Store


def test_defaultproviderfactories_non_empty() -> None:
    """It is not empty."""
    assert defaultproviderfactories


def test_defaultproviderfactories_strings() -> None:
    """Its keys are strings."""
    assert all(
        isinstance(providername, str) for providername in defaultproviderfactories
    )


def test_defaultproviderfactories_providerfactories(store: Store) -> None:
    """Its values are provider factories."""
    url = URL("mailto:you@example.com")
    for providerfactory in defaultproviderfactories.values():
        provider = providerfactory(store, FetchMode.ALWAYS)
        assert provider(url, None) is None
