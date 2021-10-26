"""Unit tests for cutty.packages.adapters.providers.git."""
import pathlib
import string
from typing import Optional

import pygit2
import pytest
from yarl import URL

from cutty.errors import CuttyError
from cutty.packages.adapters.providers.git import gitproviderfactory
from cutty.packages.adapters.providers.git import localgitprovider
from cutty.packages.domain.locations import asurl
from cutty.packages.domain.providers import Provider
from cutty.packages.domain.stores import Store
from cutty.util.git import Repository
from tests.util.git import updatefile

signature = pygit2.Signature("you", "you@example.com")


@pytest.fixture
def url(tmp_path: pathlib.Path) -> URL:
    """Fixture for a repository."""
    path = tmp_path / "repository"
    repository = Repository.init(path)
    updatefile(path / "marker", "Lorem")

    repository.createtag("v1.0", message="Release v1.0")
    updatefile(path / "marker", "Ipsum")

    return asurl(path)


@pytest.mark.parametrize(
    ("revision", "expected"),
    [
        ("v1.0", "Lorem"),
        (None, "Ipsum"),
    ],
)
def test_local_happy(url: URL, revision: Optional[str], expected: str) -> None:
    """It provides a package from a local directory."""
    repository = localgitprovider.provide(url, revision)

    assert repository is not None

    with repository.get(revision) as package:
        text = (package.path / "marker").read_text()
        assert expected == text


def test_local_not_matching(tmp_path: pathlib.Path) -> None:
    """It returns None if the path is not a git repository."""
    url = asurl(tmp_path)
    repository = localgitprovider.provide(url)

    assert repository is None


def test_local_invalid_revision(url: URL) -> None:
    """It raises an exception."""
    with pytest.raises(CuttyError):
        localgitprovider.provide(url, "invalid")


def test_local_revision_tag(url: URL) -> None:
    """It returns the tag name."""
    repository = localgitprovider.provide(url, "HEAD^")

    assert repository is not None

    with repository.get("HEAD^") as package:
        assert package.revision == "v1.0"


def test_local_revision_commit(url: URL) -> None:
    """It returns seven or more hexadecimal digits."""
    repository = localgitprovider.provide(url)

    assert repository is not None

    with repository.get() as package:
        assert (
            package.revision is not None
            and len(package.revision) >= 7
            and all(c in string.hexdigits for c in package.revision)
        )


@pytest.fixture
def gitprovider(store: Store) -> Provider:
    """Return a git provider."""
    return gitproviderfactory(store)


@pytest.mark.parametrize(
    ("revision", "expected"),
    [
        ("v1.0", "Lorem"),
        (None, "Ipsum"),
    ],
)
def test_remote_happy(
    gitprovider: Provider, url: URL, revision: Optional[str], expected: str
) -> None:
    """It fetches a git repository into storage."""
    repository = gitprovider.provide(url, revision)

    assert repository is not None

    with repository.get(revision) as package:
        text = (package.path / "marker").read_text()
        assert expected == text


def test_remote_revision_tag(gitprovider: Provider, url: URL) -> None:
    """It returns the tag name."""
    repository = gitprovider.provide(url, "HEAD^")

    assert repository is not None

    with repository.get("HEAD^") as package:
        assert package.revision == "v1.0"


def test_remote_revision_commit(gitprovider: Provider, url: URL) -> None:
    """It returns seven or more hexadecimal digits."""
    repository = gitprovider.provide(url)

    assert repository is not None

    with repository.get() as package:
        assert (
            package.revision is not None
            and len(package.revision) >= 7
            and all(c in string.hexdigits for c in package.revision)
        )


def test_remote_not_matching(gitprovider: Provider) -> None:
    """It returns None if the URL scheme is not recognized."""
    repository = gitprovider.provide(URL("mailto:you@example.com"))

    assert repository is None
