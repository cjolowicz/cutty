"""Unit tests for cutty.repositories.adapters.providers.git."""
import pathlib
from typing import Optional

import pygit2
import pytest
from yarl import URL

from cutty.repositories.adapters.providers.git import gitproviderfactory
from cutty.repositories.adapters.providers.git import localgitprovider
from cutty.repositories.domain.fetchers import FetchMode
from cutty.repositories.domain.locations import asurl
from cutty.repositories.domain.stores import Store
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


@pytest.mark.parametrize(("revision", "expected"), [("v1.0", "Lorem"), (None, "Ipsum")])
def test_localgitprovider_happy(
    url: URL, revision: Optional[str], expected: str
) -> None:
    """It provides a repository from a local directory."""
    repository = localgitprovider(url, revision)
    assert repository is not None

    text = (repository.path / "marker").read_text()
    assert text == expected


def test_localgitprovider_not_matching(tmp_path: pathlib.Path) -> None:
    """It returns None if the path is not a git repository."""
    url = asurl(tmp_path)
    repository = localgitprovider(url, None)
    assert repository is None


def test_localgitprovider_revision_tag(url: URL) -> None:
    """It returns the tag name."""
    repository = localgitprovider(url, "HEAD^")
    assert repository is not None
    assert repository.revision == "v1.0"


@pytest.mark.parametrize(("revision", "expected"), [("v1.0", "Lorem"), (None, "Ipsum")])
def test_gitproviderfactory_happy(
    store: Store, url: URL, revision: Optional[str], expected: str
) -> None:
    """It fetches a git repository into storage."""
    gitprovider = gitproviderfactory(store, FetchMode.ALWAYS)
    repository = gitprovider(url, revision)
    assert repository is not None

    text = (repository.path / "marker").read_text()
    assert text == expected


def test_gitproviderfactory_not_matching(store: Store) -> None:
    """It returns None if the URL scheme is not recognized."""
    url = URL("mailto:you@example.com")
    gitprovider = gitproviderfactory(store, FetchMode.ALWAYS)
    repository = gitprovider(url, None)
    assert repository is None
