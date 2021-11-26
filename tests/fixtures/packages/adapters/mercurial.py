"""Fixtures for cutty.packages.adapters.providers.mercurial."""
import pytest

from cutty.packages.adapters.fetchers.mercurial import findhg
from cutty.packages.adapters.fetchers.mercurial import Hg
from cutty.packages.adapters.fetchers.mercurial import HgNotFoundError


@pytest.fixture(scope="session")
def hg() -> Hg:
    """Fixture for a hg command."""
    try:
        return findhg(env={"HGUSER": "You <you@example.com>"})
    except HgNotFoundError:  # pragma: no cover
        pytest.skip("cannot locate hg")
