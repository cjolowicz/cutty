"""Fixtures for cutty.packages.adapters.providers.mercurial."""
import pytest

from cutty.packages.adapters.fetchers.mercurial import findhg
from cutty.packages.adapters.fetchers.mercurial import Hg
from cutty.packages.adapters.fetchers.mercurial import HgNotFoundError


@pytest.fixture(scope="session")
def hg() -> Hg:
    """Fixture for a hg command."""
    try:
        return findhg(env={"HGUSER": "you@example.com"})
    except HgNotFoundError:
        pytest.skip("cannot locate hg")
