"""Unit tests for cutty.repositories.domain.providers."""
import json
import pathlib
from typing import Optional

import pytest
from yarl import URL

from cutty.repositories.domain.fetchers import Fetcher
from cutty.repositories.domain.fetchers import FetchMode
from cutty.repositories.domain.locations import asurl
from cutty.repositories.domain.matchers import Matcher
from cutty.repositories.domain.mounters import Mounter
from cutty.repositories.domain.providers import LocalProvider
from cutty.repositories.domain.providers import Provider
from cutty.repositories.domain.providers import RemoteProviderFactory
from cutty.repositories.domain.registry import provide
from cutty.repositories.domain.revisions import Revision
from cutty.repositories.domain.stores import Store
from tests.fixtures.repositories.domain.providers import dictprovider
from tests.fixtures.repositories.domain.providers import nullprovider


pytest_plugins = [
    "tests.fixtures.repositories.domain.fetchers",
    "tests.fixtures.repositories.domain.matchers",
    "tests.fixtures.repositories.domain.mounters",
]


@pytest.mark.parametrize(
    "providers",
    [
        [],
        [nullprovider],
        [nullprovider, nullprovider],
    ],
)
def test_provide_fail(providers: list[Provider]) -> None:
    """It raises an exception."""
    with pytest.raises(Exception):
        provide(providers, URL())


@pytest.mark.parametrize(
    "providers",
    [
        [dictprovider({})],
        [dictprovider({}), nullprovider],
        [nullprovider, dictprovider({})],
        [dictprovider({}), dictprovider({"marker": ""})],
    ],
)
def test_provide_pass(providers: list[Provider]) -> None:
    """It returns a path to the filesystem."""
    repository = provide(providers, URL())
    assert repository.path.is_dir()
    assert not (repository.path / "marker").is_file()


def test_localprovider_not_local(url: URL, diskmounter: Mounter) -> None:
    """It returns None if the location is not local."""
    provider = LocalProvider(match=lambda path: True, mount=diskmounter)

    assert provider(url) is None


def test_localprovider_not_matching(
    tmp_path: pathlib.Path, diskmounter: Mounter
) -> None:
    """It returns None if the provider does not match."""
    url = asurl(tmp_path)
    provider = LocalProvider(match=lambda path: False, mount=diskmounter)

    assert provider(url) is None


def test_localprovider_inexistent_path(diskmounter: Mounter) -> None:
    """It returns None if the location is an inexistent path."""
    provider = LocalProvider(match=lambda path: True, mount=diskmounter)
    path = pathlib.Path("/no/such/file/or/directory")

    assert provider(path) is None


def test_localprovider_path(tmp_path: pathlib.Path, diskmounter: Mounter) -> None:
    """It returns the repository."""
    repository = tmp_path / "repository"
    repository.mkdir()
    (repository / "marker").touch()

    url = asurl(repository)
    provider = LocalProvider(match=lambda path: True, mount=diskmounter)
    repository2 = provider(url)

    assert repository2 is not None
    [entry] = repository2.path.iterdir()
    assert entry.name == "marker"


def test_localprovider_revision(tmp_path: pathlib.Path, diskmounter: Mounter) -> None:
    """It raises an exception if the mounter does not support revisions."""
    url = asurl(tmp_path)
    provider = LocalProvider(match=lambda path: True, mount=diskmounter)

    with pytest.raises(Exception):
        provider(url, "v1.0.0")


def test_localprovider_repository_revision(
    tmp_path: pathlib.Path, diskmounter: Mounter
) -> None:
    """It determines the revision of the repository."""

    def getrevision(
        path: pathlib.Path, revision: Optional[Revision]
    ) -> Optional[Revision]:
        """Return the contents of the VERSION file."""
        return (path / "VERSION").read_text().strip()

    provider = LocalProvider(
        match=lambda _: True, mount=diskmounter, getrevision=getrevision
    )

    path = tmp_path / "repository"
    path.mkdir()
    (path / "VERSION").write_text("1.0")

    repository = provider(asurl(path))

    assert repository is not None
    assert "1.0" == repository.revision


def test_remoteproviderfactory_no_fetchers(store: Store) -> None:
    """It returns None if there are no fetchers."""
    providerfactory = RemoteProviderFactory(fetch=[])
    provider = providerfactory(store)
    assert provider(URL()) is None


def test_remoteproviderfactory_no_matching_fetchers(
    store: Store, nullfetcher: Fetcher
) -> None:
    """It returns None if all fetchers return None."""
    providerfactory = RemoteProviderFactory(fetch=[nullfetcher])
    provider = providerfactory(store)
    assert provider(URL()) is None


def test_remoteproviderfactory_happy(
    store: Store, emptyfetcher: Fetcher, url: URL
) -> None:
    """It mounts a filesystem for the fetched repository."""
    providerfactory = RemoteProviderFactory(fetch=[emptyfetcher])
    provider = providerfactory(store)
    repository = provider(url)

    assert repository is not None


def test_remoteproviderfactory_repository_revision(
    store: Store, emptyfetcher: Fetcher, url: URL
) -> None:
    """It returns the repository revision."""

    def getrevision(
        path: pathlib.Path, revision: Optional[Revision]
    ) -> Optional[Revision]:
        """Return a fake version."""
        return "v1.0"

    providerfactory = RemoteProviderFactory(
        fetch=[emptyfetcher], getrevision=getrevision
    )
    provider = providerfactory(store)
    repository = provider(url)

    assert repository is not None and repository.revision == "v1.0"


def test_remoteproviderfactory_not_matching(
    store: Store, emptyfetcher: Fetcher, url: URL, nullmatcher: Matcher
) -> None:
    """It returns None if the provider itself does not match."""
    providerfactory = RemoteProviderFactory(match=nullmatcher, fetch=[emptyfetcher])
    provider = providerfactory(store)
    assert provider(url) is None


def test_remoteproviderfactory_mounter(
    store: Store, emptyfetcher: Fetcher, url: URL, jsonmounter: Mounter
) -> None:
    """It uses the mounter to mount the filesystem."""
    url = url.with_name(f"{url.name}.json")
    revision = "v1.0.0"
    if path := emptyfetcher(url, store, revision, FetchMode.ALWAYS):
        text = json.dumps({revision: {"marker": "Lorem"}})
        path.write_text(text)

    providerfactory = RemoteProviderFactory(fetch=[emptyfetcher], mount=jsonmounter)
    provider = providerfactory(store)
    repository = provider(url, revision)

    assert repository is not None
    assert (repository.path / "marker").read_text() == "Lorem"


def test_remoteproviderfactory_inexistent_path(
    store: Store, emptyfetcher: Fetcher, nullmatcher: Matcher
) -> None:
    """It returns None if the location is an inexistent path."""
    providerfactory = RemoteProviderFactory(fetch=[emptyfetcher])
    provider = providerfactory(store)
    path = pathlib.Path("/no/such/file/or/directory")

    assert provider(path) is None
