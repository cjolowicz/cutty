"""Fixtures for cutty.repositories.domain.stores."""
import pathlib

import pytest
from yarl import URL

from cutty.repositories.domain.stores import Store


@pytest.fixture
def store(tmp_path: pathlib.Path) -> Store:
    """Fixture for a store."""
    path = tmp_path / "store"
    path.mkdir()

    def _(url: URL) -> pathlib.Path:
        return path

    return _
