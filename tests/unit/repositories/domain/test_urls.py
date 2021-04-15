"""Unit tests for cutty.repositories.domain.urls."""
import os
import platform
from collections.abc import Iterator
from pathlib import Path

import pytest
from yarl import URL

from cutty.repositories.domain.urls import aspath
from cutty.repositories.domain.urls import asurl
from cutty.repositories.domain.urls import parseurl
from cutty.repositories.domain.urls import realpath


@pytest.fixture(autouse=True)
def temporary_working_directory(tmp_path: Path) -> Iterator[Path]:
    """Change the working directory to a temporary location."""
    path = tmp_path / "pristine"
    path.mkdir()

    cwd = Path.cwd()
    os.chdir(path)
    yield path
    os.chdir(cwd)


@pytest.mark.parametrize(
    "path",
    [
        Path("/"),
        Path("relative"),
        Path("a?b"),
    ],
    ids=str,
)
def test_asurl_aspath_roundtrip(path: Path) -> None:
    """It returns the canonical path."""
    assert aspath(asurl(path)) == realpath(path)


@pytest.mark.parametrize(
    "url",
    [
        URL("http://example.com"),
        URL("file:///path/to/dir#fragment"),
        URL("file:///path/to/dir?query"),
        URL("/path/to/dir#fragment"),
        URL("/path/to/dir?query"),
    ],
    ids=str,
)
def test_aspath_invalid(url: URL) -> None:
    """It raises an exception."""
    with pytest.raises(ValueError):
        aspath(url)


@pytest.mark.skipif(platform.system() != "Windows", reason="Windows only")
@pytest.mark.parametrize(
    ("url", "expected"),
    [
        (URL("file:///C:/dir/file"), Path(r"C:\dir\file")),
        (URL("file://host/share/file"), Path(r"\\host\share\file")),
    ],
)
def test_aspath_windows(url: URL, expected: Path) -> None:
    """It translates drive letters and hosts."""
    assert aspath(url) == expected


@pytest.mark.parametrize(
    "path,expected",
    [
        (Path("/"), URL("file:///")),
        (Path("/path/to/dir"), URL("file:///path/to/dir")),
    ],
    ids=str,
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
    ids=str,
)
def test_asurl_roundtrip(path: Path) -> None:
    """The path part of the URL contains the canonical path."""
    assert realpath(path) == Path(asurl(path).path)


@pytest.mark.parametrize(
    "location,expected",
    [
        ("/", URL("file:///")),
        ("https://example.com/repository", URL("https://example.com/repository")),
        ("a:b", URL("a:b")),
    ],
    ids=str,
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


@pytest.mark.parametrize(
    "name",
    [
        "http://example.com",
    ],
)
def test_parseurl_path_is_url(name: str) -> None:
    """It parses an existing path that is indistinguishable from a URL."""
    path = Path(name)
    path.parent.mkdir(parents=True)
    path.touch()

    url = parseurl(name)

    assert url.scheme == "file"
    assert Path(url.path) == realpath(path)


@pytest.mark.parametrize(
    "name",
    [
        "a#b",
        "a?b",
    ],
)
def test_parseurl_no_scheme(name: str) -> None:
    """Locations without schemes are interpreted as paths even if they don't exist."""
    url = parseurl(name)

    assert url.scheme == "file"
    assert Path(url.path) == realpath(Path(name))
