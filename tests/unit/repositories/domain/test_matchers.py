"""Unit tests for cutty.repositories.domain.matchers."""
import pytest
from yarl import URL

from cutty.repositories.domain.matchers import scheme


@pytest.mark.parametrize(
    ("schemes", "url"),
    [
        (("https", "http"), URL("https://example.com/")),
        (("file",), URL("/home/user/repository")),
    ],
)
def test_scheme_pass(url: URL, schemes: tuple[str]) -> None:
    """It matches the URL."""
    match = scheme(*schemes)
    assert match(url)


@pytest.mark.parametrize(
    ("schemes", "url"),
    [
        (("http", "ftp"), URL("https://example.com/")),
        (("https", "http", "ftp"), URL("/home/user/repository")),
    ],
)
def test_scheme_fail(url: URL, schemes: tuple[str]) -> None:
    """It does not match the URL."""
    match = scheme(*schemes)
    assert not match(url)
