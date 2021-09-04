"""Unit tests for cutty.repositories.adapters.fetchers.git."""
import pathlib
from textwrap import dedent
from typing import Iterator

import pygit2
import pytest
from yarl import URL

from cutty.filesystems.adapters.git import GitFilesystem
from cutty.filesystems.domain.path import Path
from cutty.repositories.adapters.fetchers.git import gitfetcher
from cutty.repositories.adapters.fetchers.git import GitFetcherError
from cutty.repositories.domain.fetchers import FetchMode
from cutty.repositories.domain.locations import aspath
from cutty.repositories.domain.locations import asurl
from cutty.repositories.domain.stores import Store
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
    removefile(aspath(url) / "marker")

    # Second fetch.
    destination = gitfetcher(url, store, None, FetchMode.ALWAYS)
    assert destination is not None

    # Check that the marker file is gone.
    path = Path("marker", filesystem=GitFilesystem(destination))
    assert path is not None
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
    destination = gitfetcher(url, store, None, FetchMode.ALWAYS)
    assert destination is not None
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
        gitfetcher(asurl(path), store, None, FetchMode.ALWAYS)


@pytest.mark.parametrize(
    ("url", "posixmessage", "windowsmessage"),
    [
        (
            URL("https://example.invalid/repository.git"),
            "failed to resolve address for example.invalid",
            "failed to send request: The server name or address could not be resolved",
        ),
        (
            URL("https://example.com/repository.git"),
            "unexpected http status code: 404",
            "request failed with status code: 404",
        ),
        (
            URL("https://example.com/index.html"),
            "invalid content-type: 'text/html; charset=UTF-8'",
            "received unexpected content-type",
        ),
        (
            URL("https://www.mercurial-scm.org/repo/hg/"),
            "unexpected http status code: 400",
            "request failed with status code: 400",
        ),
    ],
)
def test_fetch_error(
    url: URL, store: Store, posixmessage: str, windowsmessage: str
) -> None:
    """It raises an exception with libgit2's error message."""
    with pytest.raises(GitFetcherError) as exceptioninfo:
        gitfetcher(url, store, None, FetchMode.ALWAYS)

    assert url == exceptioninfo.value.url
    assert any(
        message in exceptioninfo.value.message
        for message in (posixmessage, windowsmessage)
    )
