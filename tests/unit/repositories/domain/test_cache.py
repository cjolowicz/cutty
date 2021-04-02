"""Unit tests for cutty.repositories.domain.cache."""
import datetime
from pathlib import Path

import pytest
from yarl import URL

from cutty.repositories.domain.cache import CacheRecord
from cutty.repositories.domain.cache import hashurl
from cutty.repositories.domain.cache import RepositoryCache


@pytest.fixture
def url() -> URL:
    """Fixture for a URL."""
    return URL("https://example.com/repository.git")


@pytest.fixture
def record(tmp_path: Path, url: URL) -> CacheRecord:
    """Fixture for a cache record."""
    timestamp = datetime.datetime.fromisoformat("2017-05-25T07:00:00+02:00")
    return CacheRecord(tmp_path, url, "git", timestamp)


def test_cacherecord_roundtrip(record: CacheRecord) -> None:
    """It roundtrips."""
    record.dump()
    assert record == CacheRecord.load(record.path)


@pytest.mark.parametrize(
    "url",
    [
        URL("https://example.com/repository.git"),
        URL("file:///tmp/repository.git"),
        URL("/tmp/repository.git"),
    ],
    ids=str,
)
def test_hashurl(url: URL) -> None:
    """It creates an ASCII digest."""
    digest = hashurl(url)
    assert len(digest) > 32
    assert digest.isascii()


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
def cache(tmp_path: Path, timer: FakeTimer) -> RepositoryCache:
    """Fixture for a repository cache."""
    return RepositoryCache(tmp_path, timer=timer)


def test_cache_get_not_found(cache: RepositoryCache, url: URL) -> None:
    """It returns None if the cache record was not found."""
    assert cache.get(url) is None


def test_cache_allocate_get(cache: RepositoryCache, url: URL) -> None:
    """It allocates and retrieves a cache record."""
    record = cache.allocate(url, provider="git")
    assert record == cache.get(url)


def test_cache_allocate_timer(
    cache: RepositoryCache, url: URL, timer: FakeTimer
) -> None:
    """It stores the current time."""
    record = cache.allocate(url, provider="git")
    assert record.updated == timer.now


def test_cache_allocate_twice(cache: RepositoryCache, url: URL) -> None:
    """It raises an exception."""
    cache.allocate(url, provider="git")
    with pytest.raises(FileExistsError):
        cache.allocate(url, provider="hg")  # the provider does not matter!


def test_cache_get_timer(cache: RepositoryCache, url: URL, timer: FakeTimer) -> None:
    """It updates the timestamp."""
    record_0 = cache.allocate(url, provider="git")
    timer.tick()
    record = cache.get(url)
    assert record is not None
    assert record.updated == timer.now
    assert record.updated != record_0.updated


def test_cache_list_empty(cache: RepositoryCache) -> None:
    """It does not yield anything."""
    records = cache.list()
    assert not list(records)


def test_cache_list_something(
    cache: RepositoryCache, url: URL, timer: FakeTimer
) -> None:
    """It yields the allocated records."""
    first = cache.allocate(url.with_host("host1"), provider="git")
    timer.tick()
    second = cache.allocate(url.with_host("host2"), provider="git")

    records = iter(sorted(cache.list(), key=lambda record: record.updated))

    assert next(records) == first
    assert next(records) == second
    assert not list(records)


def test_cache_clean_empty(cache: RepositoryCache, timer: FakeTimer) -> None:
    """It does nothing."""
    cutoff = timer.now - datetime.timedelta(seconds=1)
    cache.clean(cutoff)


def test_cache_clean_something(
    cache: RepositoryCache, url: URL, timer: FakeTimer
) -> None:
    """It removes records older than the cutoff."""
    first = cache.allocate(url.with_host("host1"), provider="git")

    timer.tick()
    cutoff = timer.now

    second = cache.allocate(url.with_host("host2"), provider="git")

    cache.clean(cutoff)

    records = list(cache.list())

    assert first not in records
    assert second in records
