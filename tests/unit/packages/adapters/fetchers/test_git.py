"""Unit tests for cutty.packages.adapters.fetchers.git."""
import pathlib
from textwrap import dedent
from typing import Iterator

import pygit2
import pytest
from yarl import URL

from cutty.errors import CuttyError
from cutty.filesystems.adapters.git import GitFilesystem
from cutty.filesystems.domain.path import Path
from cutty.packages.adapters.fetchers.git import gitfetcher
from cutty.packages.domain.locations import aspath
from cutty.packages.domain.locations import asurl
from cutty.packages.domain.stores import Store
from cutty.util.git import Repository
from tests.util.git import removefile
from tests.util.git import updatefile


signature = pygit2.Signature("you", "you@example.com")


@pytest.fixture
def url(tmp_path: pathlib.Path) -> URL:
    """Fixture for a repository."""
    path = tmp_path / "repository"
    Repository.init(path)
    updatefile(path / "marker", "Lorem")

    return asurl(path)


def test_happy(url: URL, store: Store) -> None:
    """It clones the git repository."""
    destination = gitfetcher.fetch(url, store)
    assert destination is not None

    path = Path("marker", filesystem=GitFilesystem(destination))
    assert path.read_text() == "Lorem"


def test_not_matched(store: Store) -> None:
    """It returns None if the URL does not use a recognized scheme."""
    url = URL("mailto:you@example.com")
    assert not gitfetcher.match(url)


def test_update(url: URL, store: Store) -> None:
    """It updates the repository from a previous fetch."""
    # First fetch.
    gitfetcher.fetch(url, store)

    # Remove the marker file.
    removefile(aspath(url) / "marker")

    # Second fetch.
    destination = gitfetcher.fetch(url, store)

    # Check that the marker file is gone.
    path = Path("marker", filesystem=GitFilesystem(destination))
    assert not (path / "marker").is_file()


@pytest.fixture
def custom_default_branch(tmp_path: pathlib.Path) -> Iterator[str]:
    """Fixture simulating custom ``init.defaultBranch`` in git config."""
    text = """
    [init]
        defaultBranch = teapot
    """

    gitconfig = tmp_path / "home" / ".gitconfig"
    gitconfig.parent.mkdir()
    gitconfig.write_text(dedent(text))

    searchpath = pygit2.option(
        pygit2.GIT_OPT_GET_SEARCH_PATH,
        pygit2.GIT_CONFIG_LEVEL_GLOBAL,
    )

    pygit2.option(
        pygit2.GIT_OPT_SET_SEARCH_PATH,
        pygit2.GIT_CONFIG_LEVEL_GLOBAL,
        str(gitconfig.parent),
    )

    yield "teapot"

    pygit2.option(
        pygit2.GIT_OPT_SET_SEARCH_PATH,
        pygit2.GIT_CONFIG_LEVEL_GLOBAL,
        searchpath,
    )


def test_broken_head_after_clone(
    url: URL, store: Store, custom_default_branch: str
) -> None:
    """It works around a bug in libgit2 resulting in a broken HEAD reference."""
    destination = gitfetcher.fetch(url, store)
    repository = Repository.open(destination)
    assert repository.head.name != custom_default_branch


def test_broken_head_after_clone_unexpected_branch(
    tmp_path: pathlib.Path, store: Store, custom_default_branch: str
) -> None:
    """It crashes if the default branch is not master or main."""
    path = tmp_path / "repository"
    repository = Repository.init(path, head="refs/heads/whoops")
    repository.commit()

    with pytest.raises(KeyError):
        gitfetcher.fetch(asurl(path), store)


def test_fetch_error(store: Store) -> None:
    """It raises an exception with libgit2's error message."""
    url = URL("https://example.invalid/repository.git")
    with pytest.raises(CuttyError):
        gitfetcher.fetch(url, store)
