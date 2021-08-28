"""Unit tests for cutty.repositories.domain.providers."""
import json
import pathlib
from collections.abc import Callable
from typing import Any
from typing import Optional

import pytest
from yarl import URL

from cutty.filesystems.adapters.dict import DictFilesystem
from cutty.filesystems.adapters.disk import DiskFilesystem
from cutty.filesystems.domain.filesystem import Filesystem
from cutty.filesystems.domain.path import Path
from cutty.repositories.domain.fetchers import Fetcher
from cutty.repositories.domain.fetchers import FetchMode
from cutty.repositories.domain.locations import asurl
from cutty.repositories.domain.locations import Location
from cutty.repositories.domain.mounters import unversioned_mounter
from cutty.repositories.domain.providers import LocalProvider
from cutty.repositories.domain.providers import Provider
from cutty.repositories.domain.providers import remoteproviderfactory
from cutty.repositories.domain.registry import provide
from cutty.repositories.domain.repository import Repository
from cutty.repositories.domain.revisions import Revision
from cutty.repositories.domain.stores import Store


pytest_plugins = ["tests.fixtures.repositories.domain.fetchers"]


ProviderFunction = Callable[[Location, Optional[Revision]], Optional[Repository]]


def provider(function: ProviderFunction) -> Provider:
    """Decorator to create a provider from a function."""

    class _Provider(Provider):
        def __call__(
            self, location: Location, revision: Optional[Revision]
        ) -> Optional[Repository]:
            return function(location, revision)

    return _Provider()


nullprovider = Provider()
"""Provider that matches no location."""


def dictprovider(mapping: Optional[dict[str, Any]] = None) -> Provider:
    """Provider that matches every URL with a repository."""

    @provider
    def _provider(
        location: Location, revision: Optional[Revision]
    ) -> Optional[Repository]:
        filesystem = DictFilesystem(mapping or {})
        if filesystem is not None:
            path = Path(filesystem=filesystem)
            return Repository(location.name, path, revision)
        return None

    return _provider


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
        provide(providers, URL(), None)


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
    repository = provide(providers, URL(), None)
    assert repository.path.is_dir()
    assert not (repository.path / "marker").is_file()


defaultmount = unversioned_mounter(DiskFilesystem)


def test_localprovider_not_local(url: URL) -> None:
    """It returns None if the location is not local."""
    provider = LocalProvider(match=lambda path: True, mount=defaultmount)

    assert provider(url, None) is None


def test_localprovider_not_matching(tmp_path: pathlib.Path) -> None:
    """It returns None if the provider does not match."""
    url = asurl(tmp_path)
    provider = LocalProvider(match=lambda path: False, mount=defaultmount)

    assert provider(url, None) is None


def test_localprovider_path(tmp_path: pathlib.Path) -> None:
    """It returns the repository."""
    repository = tmp_path / "repository"
    repository.mkdir()
    (repository / "marker").touch()

    url = asurl(repository)
    provider = LocalProvider(match=lambda path: True, mount=defaultmount)
    repository2 = provider(url, None)

    assert repository2 is not None
    [entry] = repository2.path.iterdir()
    assert entry.name == "marker"


def test_localprovider_revision(tmp_path: pathlib.Path) -> None:
    """It raises an exception if the mounter does not support revisions."""
    url = asurl(tmp_path)
    provider = LocalProvider(match=lambda path: True, mount=defaultmount)

    with pytest.raises(Exception):
        provider(url, "v1.0.0")


def test_localprovider_repository_revision(tmp_path: pathlib.Path) -> None:
    """It determines the revision of the repository."""

    def getrevision(
        path: pathlib.Path, revision: Optional[Revision]
    ) -> Optional[Revision]:
        """Return the contents of the VERSION file."""
        return (path / "VERSION").read_text().strip()

    provider = LocalProvider(
        match=lambda _: True, mount=defaultmount, getrevision=getrevision
    )

    path = tmp_path / "repository"
    path.mkdir()
    (path / "VERSION").write_text("1.0")

    repository = provider(asurl(path), None)

    assert repository is not None
    assert "1.0" == repository.revision


def test_remoteproviderfactory_no_fetchers(store: Store) -> None:
    """It returns None if there are no fetchers."""
    providerfactory = remoteproviderfactory(fetch=[])
    provider = providerfactory(store, FetchMode.ALWAYS)
    assert provider(URL(), None) is None


def nullfetcher(
    url: URL, store: Store, revision: Optional[Revision], mode: FetchMode
) -> Optional[pathlib.Path]:
    """Fetcher that matches no URL."""
    return None


def test_remoteproviderfactory_no_matching_fetchers(store: Store) -> None:
    """It returns None if all fetchers return None."""
    providerfactory = remoteproviderfactory(fetch=[nullfetcher])
    provider = providerfactory(store, FetchMode.ALWAYS)
    assert provider(URL(), None) is None


def test_remoteproviderfactory_happy(store: Store, fetcher: Fetcher, url: URL) -> None:
    """It mounts a filesystem for the fetched repository."""
    providerfactory = remoteproviderfactory(fetch=[fetcher])
    provider = providerfactory(store, FetchMode.ALWAYS)
    repository = provider(url, None)

    assert repository is not None


def test_remoteproviderfactory_repository_revision(
    store: Store, fetcher: Fetcher, url: URL
) -> None:
    """It returns the repository revision."""

    def getrevision(
        path: pathlib.Path, revision: Optional[Revision]
    ) -> Optional[Revision]:
        """Return a fake version."""
        return "v1.0"

    providerfactory = remoteproviderfactory(fetch=[fetcher], getrevision=getrevision)
    provider = providerfactory(store, FetchMode.ALWAYS)
    repository = provider(url, None)

    assert repository is not None and repository.revision == "v1.0"


def nullmatcher(url: URL) -> bool:
    """Matcher that matches no URL."""
    return False


def test_remoteproviderfactory_not_matching(
    store: Store, fetcher: Fetcher, url: URL
) -> None:
    """It returns None if the provider itself does not match."""
    providerfactory = remoteproviderfactory(match=nullmatcher, fetch=[fetcher])
    provider = providerfactory(store, FetchMode.ALWAYS)
    assert provider(url, None) is None


def jsonmounter(path: pathlib.Path, revision: Optional[Revision]) -> Filesystem:
    """Mount a dict filesystem read from JSON."""
    text = path.read_text()
    data = json.loads(text)
    return DictFilesystem(data[revision] if revision is not None else data)


def test_remoteproviderfactory_mounter(
    store: Store, fetcher: Fetcher, url: URL
) -> None:
    """It uses the mounter to mount the filesystem."""
    revision = "v1.0.0"
    url = url.with_name(f"{url.name}.json")
    data = {revision: {"marker": "Lorem"}}
    text = json.dumps(data)
    path = fetcher(url, store, revision, FetchMode.ALWAYS)
    assert path is not None  # for type narrowing
    path.write_text(text)

    providerfactory = remoteproviderfactory(fetch=[fetcher], mount=jsonmounter)
    provider = providerfactory(store, FetchMode.ALWAYS)
    repository = provider(url, revision)

    assert repository is not None
    assert (repository.path / "marker").read_text() == "Lorem"
