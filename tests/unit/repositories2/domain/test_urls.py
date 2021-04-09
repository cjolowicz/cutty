"""Unit tests for cutty.repositories2.domain.urls."""
from pathlib import Path

import pytest
from yarl import URL

from cutty.repositories2.domain.urls import asurl


@pytest.mark.parametrize(
    "path,expected",
    [
        (Path("/"), URL("file:///")),
        (Path("/path/to/dir"), URL("file:///path/to/dir")),
    ],
)
def test_asurl_valid(path: Path, expected: URL) -> None:
    """It converts the path to a URL."""
    assert asurl(path) == expected


@pytest.mark.parametrize(
    "path",
    [
        Path(),
        Path("relative"),
    ],
)
def test_asurl_roundtrip(path: Path) -> None:
    """The path part of the URL contains the resolved path."""
    assert path.resolve() == Path(asurl(path).path)
