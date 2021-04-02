"""Repository cache."""
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


@dataclass
class CacheRecord:
    """Record describing the storage entry for a repository."""

    path: pathlib.Path
    url: URL
    provider: str
    updated: datetime.datetime

    @classmethod
    def load(cls, path: pathlib.Path) -> CacheRecord:
        """Deserialize a JSON file to a CacheRecord instance."""
        text = (path / "entry.json").read_text()
        data = json.loads(text)
        return cls(
            path,
            URL(data["url"]),
            data["provider"],
            datetime.datetime.fromisoformat(data["updated"]),
        )

    def dump(self, path: pathlib.Path) -> None:
        """Serialize the entry to a JSON file."""
        data = {
            "url": str(self.url),
            "provider": self.provider,
            "updated": self.updated.isoformat(),
        }
        text = json.dumps(data)
        (path / "entry.json").write_text(text)


def hashurl(url: URL) -> str:
    """Return the hashsum for the given URL.

    This function creates a 128-character digest using the BLAKE2b hash
    algorithm.
    """
    data = str(url).encode()
    return hashlib.blake2b(data).hexdigest()


Timer = Callable[[], datetime.datetime]


class RepositoryCache:
    """Storage backend for repositories."""

    def __init__(self, path: pathlib.Path, *, timer: Timer) -> None:
        """Initialize."""
        self.path = path
        self.path.mkdir(parents=True, exist_ok=True)
        self.timer = timer

    def _getrepositorypath(self, url: URL) -> pathlib.Path:
        """Return the path to the repository."""
        hash = hashurl(url)
        return self.path / "entries" / hash[:2] / hash

    def get(self, url: URL) -> Optional[CacheRecord]:
        """Retrieve storage for a repository."""
        path = self._getrepositorypath(url)
        if not path.exists():
            return None

        record = CacheRecord.load(path)
        record.updated = self.timer()
        record.dump(path)

        return record

    def allocate(self, url: URL, *, provider: str) -> CacheRecord:
        """Allocate storage for a repository."""
        path = self._getrepositorypath(url)
        path.mkdir(parents=True)

        record = CacheRecord(path, url, provider, self.timer())
        record.dump(path)

        return record

    def list(self) -> Iterator[CacheRecord]:
        """Return the list of storage entries."""
        entries = self.path / "entries"
        if entries.exists():
            for directory in entries.iterdir():
                for path in directory.iterdir():
                    yield CacheRecord.load(path)

    def clean(self, cutoff: datetime.datetime) -> None:
        """Remove storage entries older than the given timestamp."""
        for record in self.list():
            if record.updated < cutoff:
                shutil.rmtree(record.path)
