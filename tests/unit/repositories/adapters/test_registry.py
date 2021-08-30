"""Unit tests for cutty.repositories.adapters.registry."""
from yarl import URL

from cutty.repositories.adapters.registry import defaultproviderfactories2
from cutty.repositories.domain.fetchers import FetchMode
from cutty.repositories.domain.stores import Store


def test_defaultproviderfactories_non_empty() -> None:
    """It is not empty."""
    assert defaultproviderfactories2


def test_defaultproviderfactories_providerfactories(store: Store) -> None:
    """Its items are provider factories."""
    url = URL("mailto:you@example.com")
    for providerfactory in defaultproviderfactories2:
        provider = providerfactory(store, FetchMode.ALWAYS)
        assert provider(url, None) is None
