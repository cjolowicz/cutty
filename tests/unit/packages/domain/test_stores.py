"""Unit tests for cutty.packages.domain.stores."""
from pathlib import Path

import pytest
from yarl import URL

from cutty.packages.domain.stores import defaultstore


@pytest.mark.parametrize(
    ("url", "path"),
    [
        (URL("https://example.com/repository"), Path("repository")),
        (URL("https://example.com/"), Path()),
    ],
)
def test_defaultstore(url: URL, path: Path) -> None:
    """It returns the relative path to the repository."""
    assert path == defaultstore(url)
