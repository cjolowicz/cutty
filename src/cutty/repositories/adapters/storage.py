"""Repository storage."""
from __future__ import annotations

import datetime
import hashlib
import json
import pathlib
import platform
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from typing import Iterator
from typing import Optional

from yarl import URL

from cutty.repositories.adapters.registry import defaultproviderregistry
from cutty.repositories.domain.providers import ProviderName
from cutty.repositories.domain.providers import ProviderStore
from cutty.repositories.domain.providers import RepositoryProvider
from cutty.repositories.domain.providers import repositoryprovider
from cutty.repositories.domain.stores import Store


@dataclass
class StorageRecord:
    """Record describing the storage for a repository."""

    path: pathlib.Path
    url: URL
    provider: str
    updated: datetime.datetime

    @classmethod
    def load(cls, path: pathlib.Path) -> StorageRecord:
        """Deserialize a JSON file to a record."""
        text = (path / "config.json").read_text()
        data = json.loads(text)
        return cls(
            path,
            URL(data["url"]),
            data["provider"],
            datetime.datetime.fromisoformat(data["updated"]),
        )

    def dump(self) -> None:
        """Serialize the record to a JSON file."""
        data = {
            "url": str(self.url),
            "provider": self.provider,
            "updated": self.updated.isoformat(),
        }
        text = json.dumps(data)
        (self.path / "config.json").write_text(text)


# Windows does not properly support files and directories longer than
# 260 characters. Use a smaller digest size on this platform.
DIGEST_SIZE: int = 64 if platform.system() != "Windows" else 32


def hashurl(url: URL) -> str:
    """Return the hashsum for the given URL.

    Creates a digest using the BLAKE2b hash algorithm.
    """
    data = str(url).encode()
    return hashlib.blake2b(data, digest_size=DIGEST_SIZE).hexdigest()


Timer = Callable[[], datetime.datetime]


def defaulttimer() -> datetime.datetime:
    """Return the current time in UTC."""
    return datetime.datetime.now(tz=datetime.timezone.utc)


class RepositoryStorage:
    """Storage backend for repositories."""

    def __init__(self, path: pathlib.Path, *, timer: Timer = defaulttimer) -> None:
        """Initialize."""
        self.path = path
        self.path.mkdir(parents=True, exist_ok=True)
        self.timer = timer

    def _getrepositorypath(self, url: URL, *, provider: ProviderName) -> pathlib.Path:
        """Return the path to the repository."""
        h = hashurl(url)
        return self.path / "repositories" / provider / h[:2] / h[2:]

    def get(self, url: URL, *, provider: ProviderName) -> Optional[StorageRecord]:
        """Retrieve storage for a repository."""
        path = self._getrepositorypath(url, provider=provider)
        if not path.exists():
            return None

        record = StorageRecord.load(path)
        record.updated = self.timer()
        record.dump()

        return record

    def allocate(self, url: URL, *, provider: ProviderName) -> StorageRecord:
        """Allocate storage for a repository."""
        path = self._getrepositorypath(url, provider=provider)
        path.mkdir(parents=True)

        record = StorageRecord(path, url, provider, self.timer())
        record.dump()

        return record

    def list(self) -> Iterator[StorageRecord]:
        """Return the list of storage entries."""
        repositories = self.path / "repositories"
        if repositories.exists():
            for provider in repositories.iterdir():
                for prefix in provider.iterdir():
                    for path in prefix.iterdir():
                        yield StorageRecord.load(path)

    def clean(self, cutoff: datetime.datetime) -> Iterator[StorageRecord]:
        """Remove storage entries older than the given timestamp."""
        for record in self.list():
            if record.updated < cutoff:
                yield record
                shutil.rmtree(record.path)


def getdefaultproviderstore(
    path: pathlib.Path, *, timer: Timer = defaulttimer
) -> ProviderStore:
    """Return a provider store."""
    storage = RepositoryStorage(path, timer=timer)

    def providerstore(provider: str) -> Store:
        """Return a store function for the provider."""

        def store(url: URL) -> pathlib.Path:
            """Return a storage location for the URL."""
            record = storage.get(url, provider=provider)
            if record is None:
                record = storage.allocate(url, provider=provider)
            return record.path

        return store

    return providerstore


def getdefaultrepositoryprovider(
    path: pathlib.Path, *, timer: Timer = defaulttimer
) -> RepositoryProvider:
    """Return a repository provider."""
    return repositoryprovider(
        defaultproviderregistry,
        getdefaultproviderstore(path, timer=timer),
    )
