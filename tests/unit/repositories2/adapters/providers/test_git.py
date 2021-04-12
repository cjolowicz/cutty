"""Unit tests for cutty.repositories2.adapters.providers.git."""
import pathlib
from typing import Optional

import pygit2
import pytest
from yarl import URL

from cutty.filesystems.domain.purepath import PurePath
from cutty.repositories2.adapters.providers.git import gitproviderfactory
from cutty.repositories2.adapters.providers.git import localgitprovider
from cutty.repositories2.domain.fetchers import FetchMode
from cutty.repositories2.domain.providers import ProviderStore
from cutty.repositories2.domain.urls import asurl


signature = pygit2.Signature("you", "you@example.com")


@pytest.fixture
def url(tmp_path: pathlib.Path) -> URL:
    """Fixture for a repository."""
    path = tmp_path / "repository"
    path.mkdir()
    (path / "marker").write_text("Lorem")

    repository = pygit2.init_repository(path)
    repository.index.add("marker")
    repository.create_commit(
        "HEAD",
        signature,
        signature,
        "Initial",
        repository.index.write_tree(),
        [],
    )

    repository.create_tag(
        "v1.0",
        repository.head.target,
        pygit2.GIT_OBJ_COMMIT,
        signature,
        "Release v1.0",
    )

    (path / "marker").write_text("Ipsum")
    repository.index.add("marker")
    repository.create_commit(
        "HEAD",
        signature,
        signature,
        "Update marker",
        repository.index.write_tree(),
        [repository.head.target],
    )

    return asurl(path)


@pytest.mark.parametrize(("revision", "expected"), [("v1.0", "Lorem"), (None, "Ipsum")])
def test_localgitprovider_happy(url: URL, revision: Optional[str], expected: str):
    """It provides a repository from a local directory."""
    filesystem = localgitprovider(url, revision=revision)
    text = filesystem.read_text(PurePath("marker"))
    assert text == expected


def test_localgitprovider_not_matching(tmp_path: pathlib.Path):
    """It returns None if the path is not a git repository."""
    url = asurl(tmp_path)
    filesystem = localgitprovider(url, revision=None)
    assert filesystem is None


@pytest.mark.parametrize(("revision", "expected"), [("v1.0", "Lorem"), (None, "Ipsum")])
def test_gitproviderfactory_happy(
    store: ProviderStore, url: URL, revision: Optional[str], expected: str
):
    """It fetches a git repository into storage."""
    gitprovider = gitproviderfactory(store, FetchMode.ALWAYS)
    filesystem = gitprovider(url, revision=revision)
    text = filesystem.read_text(PurePath("marker"))
    assert text == expected


def test_gitproviderfactory_not_matching(store: ProviderStore):
    """It returns None if the URL scheme is not recorgnized."""
    url = URL("mailto:you@example.com")
    gitprovider = gitproviderfactory(store, FetchMode.ALWAYS)
    filesystem = gitprovider(url, revision=None)
    assert filesystem is None
