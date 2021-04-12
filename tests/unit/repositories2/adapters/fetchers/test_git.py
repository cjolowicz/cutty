"""Unit tests for cutty.repositories2.adapters.fetchers.git."""
import pathlib

import pygit2
import pytest
from yarl import URL

from cutty.filesystems.adapters.git import GitFilesystem
from cutty.filesystems.domain.path import Path
from cutty.repositories2.adapters.fetchers.git import gitfetcher
from cutty.repositories2.domain.fetchers import FetchMode
from cutty.repositories2.domain.stores import Store
from cutty.repositories2.domain.urls import aspath
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

    return asurl(path)


def test_gitfetcher_happy(url: URL, store: Store) -> None:
    """It clones the git repository."""
    destination = gitfetcher(url, store, None, FetchMode.ALWAYS)
    assert destination is not None

    path = Path("marker", filesystem=GitFilesystem(destination))
    assert path.read_text() == "Lorem"


def test_gitfetcher_not_matched(store: Store) -> None:
    """It returns None if the URL does not use a recognized scheme."""
    url = URL("mailto:you@example.com")
    path = gitfetcher(url, store, None, FetchMode.ALWAYS)
    assert path is None


def test_gitfetcher_update(url: URL, store: Store) -> None:
    """It updates the repository from a previous fetch."""
    # First fetch.
    gitfetcher(url, store, None, FetchMode.ALWAYS)

    # Remove the marker file.
    repository = pygit2.Repository(aspath(url))
    tree = repository.head.peel(pygit2.Tree)
    repository.index.read_tree(tree)
    repository.index.remove("marker")
    repository.create_commit(
        "HEAD",
        signature,
        signature,
        "Remove the marker file",
        repository.index.write_tree(),
        [repository.head.target],
    )

    # Second fetch.
    destination = gitfetcher(url, store, None, FetchMode.ALWAYS)
    assert destination is not None

    # Check that the marker file is gone.
    path = Path("marker", filesystem=GitFilesystem(destination))
    assert path is not None
    assert not (path / "marker").is_file()
