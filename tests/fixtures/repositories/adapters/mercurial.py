"""Fixtures for cutty.repositories.adapters.providers.mercurial."""
import pytest

from cutty.repositories.adapters.fetchers.mercurial import findhg
from cutty.repositories.adapters.fetchers.mercurial import Hg


@pytest.fixture
def hg() -> Hg:
    """Fixture for a hg command."""
    try:
        return findhg()
    except RuntimeError:
        pytest.skip("cannot locate hg")
