"""Unit tests for cutty.packages.adapters.providers.git."""
import pathlib
import string
from typing import Optional

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
    repository = localgitprovider.provide(url)

    assert repository is not None

    with repository.get(revision) as package:
        text = (package.tree / "marker").read_text()
        assert expected == text


def test_local_not_matching(tmp_path: pathlib.Path) -> None:
    """It returns None if the path is not a git repository."""
    url = asurl(tmp_path)
    repository = localgitprovider.provide(url)

    assert repository is None


def test_local_invalid_revision(url: URL) -> None:
    """It raises an exception if the revision is invalid."""
    with pytest.raises(CuttyError):
        if repository := localgitprovider.provide(url):
            with repository.get("invalid"):
                pass


def test_local_revision_tag(url: URL) -> None:
    """It retrieves the tag name as the package revision."""
    repository = localgitprovider.provide(url)

    assert repository is not None

    with repository.get("HEAD^") as package:
        assert package.commit is not None and package.commit.revision == "v1.0"


def test_local_revision_commit(url: URL) -> None:
    """It retrieves the short hash as the package revision."""
    repository = localgitprovider.provide(url)

    assert repository is not None

    with repository.get() as package:
        assert (
            package.commit is not None
            and len(package.commit.revision) >= 7
            and all(c in string.hexdigits for c in package.commit.revision)
        )


def test_local_author(url: URL) -> None:
    """It retrieves the author name and email."""
    repository = localgitprovider.provide(url)

    assert repository is not None

    with repository.get() as package:
        assert package.commit is not None
        assert "You" == package.commit.author.name
        assert "you@example.com" == package.commit.author.email


def test_local_date(url: URL) -> None:
    """It retrieves the commit date."""
    repository = localgitprovider.provide(url)

    assert repository is not None

    with repository.get() as package:
        assert package.commit is not None
        assert package.commit.date


@pytest.fixture
def gitprovider(store: Store) -> Provider:
    """Fixture for a git provider."""
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
    repository = gitprovider.provide(url)

    assert repository is not None

    with repository.get(revision) as package:
        text = (package.tree / "marker").read_text()
        assert expected == text


def test_remote_revision_tag(gitprovider: Provider, url: URL) -> None:
    """It retrieves the tag name as the package revision."""
    repository = gitprovider.provide(url)

    assert repository is not None

    with repository.get("HEAD^") as package:
        assert package.commit is not None and package.commit.revision == "v1.0"


def test_remote_revision_commit(gitprovider: Provider, url: URL) -> None:
    """It retrieves the short hash as the package revision."""
    repository = gitprovider.provide(url)

    assert repository is not None

    with repository.get() as package:
        assert (
            package.commit is not None
            and len(package.commit.revision) >= 7
            and all(c in string.hexdigits for c in package.commit.revision)
        )


def test_remote_not_matching(gitprovider: Provider) -> None:
    """It returns None if the URL scheme is not recognized."""
    repository = gitprovider.provide(URL("mailto:you@example.com"))

    assert repository is None
