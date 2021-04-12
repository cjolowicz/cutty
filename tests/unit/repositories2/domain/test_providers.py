"""Unit tests for cutty.repositories2.domain.providers."""
import json
import pathlib
from typing import Any
from typing import Optional

import pytest
from yarl import URL

from cutty.filesystems.adapters.dict import DictFilesystem
from cutty.filesystems.adapters.disk import DiskFilesystem
from cutty.filesystems.domain.filesystem import Filesystem
from cutty.filesystems.domain.purepath import PurePath
from cutty.repositories2.domain.fetchers import Fetcher
from cutty.repositories2.domain.fetchers import FetchMode
from cutty.repositories2.domain.mounters import unversioned_mounter
from cutty.repositories2.domain.providers import constproviderfactory
from cutty.repositories2.domain.providers import localprovider
from cutty.repositories2.domain.providers import provide
from cutty.repositories2.domain.providers import Provider
from cutty.repositories2.domain.providers import ProviderStore
from cutty.repositories2.domain.providers import registerprovider
from cutty.repositories2.domain.providers import registerproviderfactories
from cutty.repositories2.domain.providers import registerproviderfactory
from cutty.repositories2.domain.providers import registerproviders
from cutty.repositories2.domain.providers import remoteproviderfactory
from cutty.repositories2.domain.providers import repositoryprovider
from cutty.repositories2.domain.revisions import Revision
from cutty.repositories2.domain.stores import Store
from cutty.repositories2.domain.urls import asurl


def nullprovider(url: URL, revision: Optional[Revision]) -> Optional[Filesystem]:
    """Provider that matches no URL."""
    return None


def dictprovider(mapping: Optional[dict[str, Any]] = None) -> Provider:
    """Provider that matches every URL with a filesystem."""

    def _dictprovider(url: URL, revision: Optional[Revision]) -> Optional[Filesystem]:
        return DictFilesystem(mapping or {})

    return _dictprovider


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
    path = provide(providers, URL(), None)
    assert path.is_dir()
    assert not (path / "marker").is_file()


defaultmount = unversioned_mounter(DiskFilesystem)


def test_localprovider_not_local(url: URL) -> None:
    """It returns None if the location is not local."""
    provider = localprovider(match=lambda path: True, mount=defaultmount)

    assert provider(url, None) is None


def test_localprovider_not_matching(tmp_path: pathlib.Path) -> None:
    """It returns None if the provider does not match."""
    url = asurl(tmp_path)
    provider = localprovider(match=lambda path: False, mount=defaultmount)

    assert provider(url, None) is None


def test_localprovider_path(tmp_path: pathlib.Path) -> None:
    """It returns a filesystem for the repository."""
    repository = tmp_path / "repository"
    repository.mkdir()
    (repository / "marker").touch()

    url = asurl(repository)
    provider = localprovider(match=lambda path: True, mount=defaultmount)
    filesystem = provider(url, None)

    [entry] = filesystem.iterdir(PurePath())
    assert entry == "marker"


def test_localprovider_revision(tmp_path: pathlib.Path) -> None:
    """It raises an exception if the mounter does not support revisions."""
    url = asurl(tmp_path)
    provider = localprovider(match=lambda path: True, mount=defaultmount)

    with pytest.raises(Exception):
        provider(url, "v1.0.0")


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


@pytest.fixture
def fetcher() -> Fetcher:
    """Fixture for a fetcher that simply creates the destination path."""

    def _fetcher(
        url: URL, store: Store, revision: Optional[Revision], mode: FetchMode
    ) -> Optional[pathlib.Path]:
        path = store(url) / url.name

        if path.suffix:
            path.touch()
        else:
            path.mkdir(exist_ok=True)

        return path

    return _fetcher


def test_remoteproviderfactory_happy(store: Store, fetcher: Fetcher, url: URL) -> None:
    """It mounts a filesystem for the fetched repository."""
    providerfactory = remoteproviderfactory(fetch=[fetcher])
    provider = providerfactory(store, FetchMode.ALWAYS)
    filesystem = provider(url, None)

    assert filesystem is not None


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
    path.write_text(text)

    providerfactory = remoteproviderfactory(fetch=[fetcher], mount=jsonmounter)
    provider = providerfactory(store, FetchMode.ALWAYS)
    filesystem = provider(url, revision)

    assert filesystem.read_text(PurePath("marker")) == "Lorem"


def test_registerproviderfactories_empty() -> None:
    """It creates an empty registry."""
    assert not registerproviderfactories()


def test_registerproviderfactories_add() -> None:
    """It adds entries."""
    providerfactory = constproviderfactory(nullprovider)

    registry = registerproviderfactories()
    registry = registerproviderfactory(registry, "default", providerfactory)

    assert registry == registerproviderfactories(default=providerfactory)


def test_registerproviderfactories_override() -> None:
    """It overrides existing entries."""
    providerfactory1 = constproviderfactory(nullprovider)
    providerfactory2 = constproviderfactory(dictprovider())

    registry = registerproviderfactories()
    registry = registerproviderfactory(registry, "default", providerfactory1)
    registry = registerproviderfactory(registry, "default", providerfactory2)

    assert registry.get("default") is providerfactory2


def test_registerproviders_empty() -> None:
    """It creates an empty registry."""
    assert not registerproviders()


def test_registerproviders_add() -> None:
    """It adds entries."""
    registry = registerproviders()
    registry = registerprovider(registry, "default", nullprovider)

    assert "default" in registry


def test_registerproviders_override(store: Store) -> None:
    """It overrides existing entries."""
    provider1 = nullprovider
    provider2 = dictprovider()

    registry = registerproviders()
    registry = registerprovider(registry, "default", provider1)
    registry = registerprovider(registry, "default", provider2)

    providerfactory = registry.get("default")
    provider = providerfactory(store, FetchMode.ALWAYS)

    # Check that it's provider2 (the nullprovider returns None).
    assert provider(URL(), None) is not None


def test_repositoryprovider_none(providerstore: ProviderStore, url: URL) -> None:
    """It raises an exception if the registry is empty."""
    registry = registerproviderfactories()
    provider = repositoryprovider(registry, providerstore)
    with pytest.raises(Exception):
        provider(url)


def test_repositoryprovider_happy(
    providerstore: ProviderStore, fetcher: Fetcher, url: URL
) -> None:
    """It returns a provider that allows traversing repositories."""
    providerfactory = remoteproviderfactory(fetch=[fetcher])
    registry = registerproviderfactories(default=providerfactory)
    provider = repositoryprovider(registry, providerstore)
    path = provider(url)
    assert not list(path.iterdir())


def test_repositoryprovider_with_provider_specific_url(
    providerstore: ProviderStore, fetcher: Fetcher, url: URL
) -> None:
    """It selects the provider indicated by the URL scheme."""
    url = url.with_scheme(f"null+{url.scheme}")
    registry = registerproviderfactories(
        default=remoteproviderfactory(fetch=[fetcher]),
        null=constproviderfactory(nullprovider),
    )
    provider = repositoryprovider(registry, providerstore)
    with pytest.raises(Exception):
        provider(url)
