"""Unit tests for cutty.packages.adapters.storage."""
import datetime
from pathlib import Path

import pytest
from yarl import URL

from cutty.packages.adapters.storage import defaulttimer
from cutty.packages.adapters.storage import getdefaultproviderstore
from cutty.packages.adapters.storage import hashurl
from cutty.packages.adapters.storage import PackageStorage
from cutty.packages.adapters.storage import StorageRecord
from cutty.packages.domain.registry import ProviderStore


@pytest.fixture
def url() -> URL:
    """Fixture for a URL."""
    return URL("https://example.com/repository.git")


@pytest.fixture
def record(tmp_path: Path, url: URL) -> StorageRecord:
    """Fixture for a storage record."""
    timestamp = datetime.datetime.fromisoformat("2017-05-25T07:00:00+02:00")
    return StorageRecord(tmp_path, url, "git", timestamp)


def test_storagerecord_roundtrip(record: StorageRecord) -> None:
    """It roundtrips."""
    record.dump()
    assert record == StorageRecord.load(record.path)


@pytest.mark.parametrize(
    "url",
    [
        URL("https://example.com/repository.git"),
        URL("file:///tmp/repository.git"),
        URL("/home/user/repository.git"),
    ],
    ids=str,
)
def test_hashurl(url: URL) -> None:
    """It creates an ASCII digest."""
    digest = hashurl(url)
    assert digest and digest.isascii()


def test_defaulttimer() -> None:
    """It returns the current time in UTC."""
    now = defaulttimer()
    assert now.year >= 2021
    assert now.tzinfo is datetime.timezone.utc


class FakeTimer:
    """Timer for testing."""

    def __init__(self) -> None:
        """Initialize."""
        self.now = datetime.datetime.fromtimestamp(0, tz=datetime.timezone.utc)

    def __call__(self) -> datetime.datetime:
        """Return the current timestamp."""
        return self.now

    def tick(self) -> None:
        """Advance the timer by one second."""
        self.now += datetime.timedelta(seconds=1)


@pytest.fixture
def timer() -> FakeTimer:
    """Fixture for a timer."""
    return FakeTimer()


@pytest.fixture
def storage(tmp_path: Path, timer: FakeTimer) -> PackageStorage:
    """Fixture for a package storage."""
    path = tmp_path / "package-storage"
    return PackageStorage(path, timer=timer)


def test_storage_get_not_found(storage: PackageStorage, url: URL) -> None:
    """It returns None if the storage record was not found."""
    assert storage.get(url, provider="git") is None


def test_storage_allocate_get(storage: PackageStorage, url: URL) -> None:
    """It allocates and retrieves a storage record."""
    record = storage.allocate(url, provider="git")
    assert record == storage.get(url, provider="git")


def test_storage_allocate_timer(
    storage: PackageStorage, url: URL, timer: FakeTimer
) -> None:
    """It stores the current time."""
    record = storage.allocate(url, provider="git")
    assert record.updated == timer.now


def test_storage_allocate_twice(storage: PackageStorage, url: URL) -> None:
    """It raises an exception."""
    storage.allocate(url, provider="git")
    with pytest.raises(FileExistsError):
        storage.allocate(url, provider="git")


def test_storage_allocate_same_url_different_provider(
    storage: PackageStorage, url: URL
) -> None:
    """It allocates separate records."""
    storage.allocate(url, provider="git")
    storage.allocate(url, provider="hg")

    assert {record.provider for record in storage.list()} == {"git", "hg"}


def test_storage_get_timer(storage: PackageStorage, url: URL, timer: FakeTimer) -> None:
    """It updates the timestamp."""
    record_0 = storage.allocate(url, provider="git")
    timer.tick()
    record = storage.get(url, provider="git")

    assert record is not None
    assert record.updated == timer.now
    assert record.updated != record_0.updated


def test_storage_list_empty(storage: PackageStorage) -> None:
    """It does not yield anything."""
    records = storage.list()
    assert not list(records)


def test_storage_list_something(
    storage: PackageStorage, url: URL, timer: FakeTimer
) -> None:
    """It yields the allocated records."""
    first = storage.allocate(url.with_host("host1"), provider="git")
    timer.tick()
    second = storage.allocate(url.with_host("host2"), provider="git")

    records = iter(sorted(storage.list(), key=lambda record: record.updated))

    assert next(records) == first
    assert next(records) == second
    assert not list(records)


def test_storage_clean_empty(storage: PackageStorage, timer: FakeTimer) -> None:
    """It does nothing."""
    cutoff = timer.now - datetime.timedelta(seconds=1)
    records = storage.clean(cutoff)

    assert not list(records)


def test_storage_clean_something(
    storage: PackageStorage, url: URL, timer: FakeTimer
) -> None:
    """It removes records older than the cutoff."""
    first = storage.allocate(url.with_host("host1"), provider="git")

    timer.tick()
    cutoff = timer.now

    second = storage.allocate(url.with_host("host2"), provider="git")

    records = list(storage.clean(cutoff))

    assert first in records
    assert second not in records

    records = list(storage.list())

    assert first not in records
    assert second in records


@pytest.fixture
def defaultproviderstore(tmp_path: Path, timer: FakeTimer) -> ProviderStore:
    """Fixture for a provider store."""
    return getdefaultproviderstore(tmp_path, timer=timer)


def test_getdefaultproviderstore_exists(
    defaultproviderstore: ProviderStore, url: URL
) -> None:
    """It returns a valid filesystem path."""
    store = defaultproviderstore("git")
    path = store(url)

    assert path.exists()


def test_getdefaultproviderstore_idempotent(
    defaultproviderstore: ProviderStore, url: URL
) -> None:
    """It returns the same path each time."""
    store = defaultproviderstore("git")

    assert store(url) == store(url)
