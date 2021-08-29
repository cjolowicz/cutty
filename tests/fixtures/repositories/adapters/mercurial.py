"""Fixtures for cutty.repositories.adapters.providers.mercurial."""
import pathlib
import subprocess  # noqa: S404
from typing import Optional

import pytest

from cutty.repositories.adapters.fetchers.mercurial import findhg
from cutty.repositories.adapters.fetchers.mercurial import Hg


@pytest.fixture
def hg() -> Hg:
    """Fixture for a hg command."""
    hg = findhg()

    def _hg(
        *args: str, cwd: Optional[pathlib.Path] = None
    ) -> subprocess.CompletedProcess[str]:
        try:
            return hg(*args, cwd=cwd)
        except RuntimeError:
            pytest.skip("cannot locate hg")

    return _hg
