"""Unit tests for cutty.repositories2.domain.urls."""
import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from yarl import URL

from cutty.repositories2.domain.urls import asurl
from cutty.repositories2.domain.urls import parseurl


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


@pytest.mark.parametrize(
    "location,expected",
    [
        ("/", URL("file:///")),
        ("https://example.com/repository", URL("https://example.com/repository")),
    ],
)
def test_parseurl_normal(location: str, expected: URL) -> None:
    """It parses the URL as expected."""
    assert parseurl(location) == expected


@pytest.mark.parametrize(
    "name",
    [
        "a:b",
        "a?b",
        "a#b",
        "data:,",
    ],
)
def test_parseurl_path_with_special_characters(tmp_path: Path, name: str) -> None:
    """It parses an existing path with URL-special characters."""
    path = tmp_path / name
    path.touch()

    url = parseurl(str(path))

    assert url.scheme == "file"
    assert url.name == name


@pytest.fixture
def tmp_cwd(tmp_path: Path) -> Iterator[Path]:
    """Fixture for changing the working directory to a temporary location."""
    cwd = Path.cwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(cwd)


@pytest.mark.parametrize(
    "name",
    [
        "http://example.com",
    ],
)
def test_parseurl_path_is_url(tmp_cwd: Path, name: str) -> None:
    """It parses an existing path that is indistinguishable from a URL."""
    path = Path(name)
    path.parent.mkdir(parents=True)
    path.touch()

    url = parseurl(str(path))

    assert url.scheme == "file"
    assert Path(url.path) == path.resolve()
