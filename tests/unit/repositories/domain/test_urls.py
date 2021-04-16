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


onlywindows = pytest.mark.skipif(platform.system() != "Windows", reason="Windows only")
skipwindows = pytest.mark.skipif(platform.system() == "Windows", reason="POSIX only")


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
        Path(),
        Path("/"),
        Path("relative"),
        pytest.param(Path("a?b"), marks=skipwindows),
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


@onlywindows
@pytest.mark.parametrize(
    ("url", "expected"),
    [
        (URL("file:///dir/file"), Path("\\dir\\file")),
        (URL("file:///C:/dir/file"), Path("C:\\dir\\file")),
        (URL("file://host/share/file"), Path("\\\\host\\share\\file")),
    ],
)
def test_aspath_windows(url: URL, expected: Path) -> None:
    """It translates drive letters and hosts."""
    assert aspath(url) == expected


@pytest.mark.parametrize(
    "path,expected",
    [
        pytest.param(Path("/"), URL("file:///"), marks=skipwindows),
        pytest.param(Path("C:\\"), URL("file:///C:/"), marks=onlywindows),
        pytest.param(
            Path("/path/to/dir"), URL("file:///path/to/dir"), marks=skipwindows
        ),
        pytest.param(
            Path("C:\\path\\to\\dir"), URL("file:///C:/path/to/dir"), marks=onlywindows
        ),
    ],
    ids=str,
)
def test_asurl_valid(path: Path, expected: URL) -> None:
    """It converts the path to a URL."""
    assert asurl(path) == expected


@pytest.mark.parametrize(
    "location,expected",
    [
        pytest.param("/", URL("file:///"), marks=skipwindows),
        pytest.param("C:\\", URL("file:///C:/"), marks=onlywindows),
        ("https://example.com/repository", URL("https://example.com/repository")),
        pytest.param("a:b", URL("a:b"), marks=skipwindows),
    ],
    ids=str,
)
def test_parseurl_normal(location: str, expected: URL) -> None:
    """It parses the URL as expected."""
    assert parseurl(location) == expected


@pytest.mark.parametrize(
    "name",
    [
        pytest.param("a:b", marks=skipwindows),
        pytest.param("a?b", marks=skipwindows),
        "a#b",
        pytest.param("data:,", marks=skipwindows),
    ],
)
def test_parseurl_path_with_special_characters(tmp_path: Path, name: str) -> None:
    """It parses an existing path with URL-special characters."""
    path = tmp_path / name
    path.touch()

    url = parseurl(str(path))

    assert url.scheme == "file"
    assert url.name == name


@skipwindows
@pytest.mark.parametrize("name", ["http://example.com"])
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
        pytest.param("a?b", marks=skipwindows),
    ],
)
def test_parseurl_no_scheme(name: str) -> None:
    """Locations without schemes are interpreted as paths even if they don't exist."""
    url = parseurl(name)

    assert url.scheme == "file"
    assert aspath(url) == realpath(Path(name))
