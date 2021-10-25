"""Fixtures for cutty.repositories.domain.matchers."""
import pytest
from yarl import URL

from cutty.packages.domain.matchers import Matcher


@pytest.fixture
def nullmatcher() -> Matcher:
    """Matcher that matches no URL."""

    def _(url: URL) -> bool:
        return False

    return _
