"""Unit tests for cutty.repositories.domain.providers."""
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
from cutty.repositories.domain.fetchers import Fetcher
from cutty.repositories.domain.fetchers import FetchMode
from cutty.repositories.domain.locations import asurl
from cutty.repositories.domain.locations import Location
from cutty.repositories.domain.mounters import unversioned_mounter
from cutty.repositories.domain.providers import asprovider2
from cutty.repositories.domain.providers import constproviderfactory
from cutty.repositories.domain.providers import localprovider
from cutty.repositories.domain.providers import provide
from cutty.repositories.domain.providers import Provider
from cutty.repositories.domain.providers import ProviderStore
from cutty.repositories.domain.providers import registerproviderfactories
from cutty.repositories.domain.providers import remoteproviderfactory
from cutty.repositories.domain.providers import remoteproviderfactory2
from cutty.repositories.domain.providers import repositoryprovider
from cutty.repositories.domain.revisions import Revision
from cutty.repositories.domain.stores import Store


def nullprovider(
    location: Location, revision: Optional[Revision]
) -> Optional[Filesystem]:
    """Provider that matches no location."""
    return None


def dictprovider(mapping: Optional[dict[str, Any]] = None) -> Provider:
    """Provider that matches every URL with a filesystem."""

    def _dictprovider(
        location: Location, revision: Optional[Revision]
    ) -> Optional[Filesystem]:
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
        providers2 = (asprovider2(provider) for provider in providers)
        provide(providers2, URL(), None)


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
    providers2 = (asprovider2(provider) for provider in providers)
    repository = provide(providers2, URL(), None)
    assert repository.path.is_dir()
    assert not (repository.path / "marker").is_file()


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
    """It returns the repository."""
    repository = tmp_path / "repository"
    repository.mkdir()
    (repository / "marker").touch()

    url = asurl(repository)
    provider = localprovider(match=lambda path: True, mount=defaultmount)
    repository2 = provider(url, None)

    assert repository2 is not None
    [entry] = repository2.path.iterdir()
    assert entry.name == "marker"


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
    assert path is not None  # for type narrowing
    path.write_text(text)

    providerfactory = remoteproviderfactory(fetch=[fetcher], mount=jsonmounter)
    provider = providerfactory(store, FetchMode.ALWAYS)
    filesystem = provider(url, revision)

    assert filesystem is not None
    assert filesystem.read_text(PurePath("marker")) == "Lorem"


def test_registerproviderfactories_empty() -> None:
    """It creates an empty registry."""
    assert not registerproviderfactories()


def test_registerproviderfactories_add() -> None:
    """It adds entries."""
    providerfactory = constproviderfactory(asprovider2(nullprovider))

    registry = registerproviderfactories()
    registry = registerproviderfactories(registry, default=providerfactory)

    assert "default" in registry


def test_registerproviderfactories_override(store: Store) -> None:
    """It overrides existing entries."""
    providerfactory1 = constproviderfactory(asprovider2(nullprovider))
    providerfactory2 = constproviderfactory(asprovider2(dictprovider()))

    registry = registerproviderfactories()
    registry = registerproviderfactories(registry, default=providerfactory1)
    registry = registerproviderfactories(registry, default=providerfactory2)

    providerfactory = registry["default"]
    provider = providerfactory(store, FetchMode.ALWAYS)

    # Check that it's provider2 (the nullprovider returns None).
    assert provider(URL(), None) is not None


def test_repositoryprovider_none(providerstore: ProviderStore, url: URL) -> None:
    """It raises an exception if the registry is empty."""
    registry = registerproviderfactories()
    provider = repositoryprovider(registry, providerstore)
    with pytest.raises(Exception):
        provider(str(url))


def test_repositoryprovider_with_url(
    providerstore: ProviderStore, fetcher: Fetcher, url: URL
) -> None:
    """It returns a provider that allows traversing repositories."""
    providerfactory = remoteproviderfactory2(fetch=[fetcher])
    registry = registerproviderfactories(default=providerfactory)
    provider = repositoryprovider(registry, providerstore)
    repository = provider(str(url))
    assert not list(repository.path.iterdir())


def test_repositoryprovider_with_path(
    tmp_path: pathlib.Path, providerstore: ProviderStore, fetcher: Fetcher
) -> None:
    """It returns a provider that allows traversing repositories."""
    directory = tmp_path / "repository"
    directory.mkdir()
    (directory / "marker").touch()

    registry = registerproviderfactories(
        default=constproviderfactory(
            localprovider(match=lambda path: True, mount=defaultmount)
        )
    )
    provider = repositoryprovider(registry, providerstore)
    repository = provider(str(directory))
    [entry] = repository.path.iterdir()

    assert entry.name == "marker"


def test_repositoryprovider_with_provider_specific_url(
    providerstore: ProviderStore, fetcher: Fetcher, url: URL
) -> None:
    """It selects the provider indicated by the URL scheme."""
    url = url.with_scheme(f"null+{url.scheme}")
    registry = registerproviderfactories(
        default=remoteproviderfactory2(fetch=[fetcher]),
        null=constproviderfactory(asprovider2(nullprovider)),
    )
    provider = repositoryprovider(registry, providerstore)
    with pytest.raises(Exception):
        provider(str(url))


def test_repositoryprovider_name_from_url(
    providerstore: ProviderStore, fetcher: Fetcher
) -> None:
    """It returns a provider that allows traversing repositories."""
    providerfactory = remoteproviderfactory2(fetch=[fetcher])
    registry = registerproviderfactories(default=providerfactory)
    provider = repositoryprovider(registry, providerstore)
    repository = provider("https://example.com/path/to/example?query#fragment")
    assert "example" == repository.name
