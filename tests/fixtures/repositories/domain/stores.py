"""Fixtures for cutty.repositories.domain.stores."""
import pathlib

import pytest

from cutty.repositories.domain.stores import Store


@pytest.fixture
def store(tmp_path: pathlib.Path) -> Store:
    """Fixture for a store."""
    return lambda url: tmp_path
