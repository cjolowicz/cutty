"""Fixtures for cutty.repositories.adapters.providers.mercurial."""
import pytest

from cutty.repositories.adapters.fetchers.mercurial import findhg
from cutty.repositories.adapters.fetchers.mercurial import Hg
from cutty.repositories.adapters.fetchers.mercurial import HgNotFoundError


@pytest.fixture(scope="session")
def hg() -> Hg:
    """Fixture for a hg command."""
    try:
        return findhg()
    except HgNotFoundError:
        pytest.skip("cannot locate hg")
