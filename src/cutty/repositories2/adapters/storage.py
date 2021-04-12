"""Repository storage."""
from __future__ import annotations

import datetime
import hashlib
import json
import pathlib
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from typing import Iterator
from typing import Optional

from yarl import URL

from cutty.repositories2.domain.providers import ProviderName
from cutty.repositories2.domain.providers import ProviderStore
from cutty.repositories2.domain.stores import Store


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


def hashurl(url: URL) -> str:
    """Return the hashsum for the given URL.

    Creates a 128-character digest using the BLAKE2b hash algorithm.
    """
    data = str(url).encode()
    return hashlib.blake2b(data).hexdigest()


Timer = Callable[[], datetime.datetime]


class RepositoryStorage:
    """Storage backend for repositories."""

    def __init__(self, path: pathlib.Path, *, timer: Timer) -> None:
        """Initialize."""
        self.path = path
        self.path.mkdir(parents=True, exist_ok=True)
        self.timer = timer

    def _getrepositorypath(self, url: URL, *, provider: ProviderName) -> pathlib.Path:
        """Return the path to the repository."""
        hash = hashurl(url)
        return self.path / "repositories" / provider / hash[:2] / hash

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


def asproviderstore(cache: RepositoryStorage) -> ProviderStore:
    """Adapt RepositoryStorage to the ProviderStore interface."""

    def _providerstore(provider: ProviderName) -> Store:
        def _store(url: URL) -> pathlib.Path:
            record = cache.get(url, provider=provider)
            if record is None:
                record = cache.allocate(url, provider=provider)
            return record.path

        return _store

    return _providerstore
