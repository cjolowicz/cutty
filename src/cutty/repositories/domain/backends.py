"""Repository backends."""
from __future__ import annotations

import datetime
import hashlib
import json
import pathlib
import shutil
from dataclasses import dataclass
from dataclasses import field
from typing import Iterator

from yarl import URL


@dataclass
class Entry:
    """Backend entry."""

    path: pathlib.Path
    url: URL
    provider: str
    updated: datetime.datetime = field(
        default_factory=lambda: datetime.datetime.now(tz=datetime.timezone.utc)
    )

    @classmethod
    def load(cls, path: pathlib.Path) -> Entry:
        """Deserialize a JSON file to an Entry instance."""
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

    def touch(self, path: pathlib.Path) -> None:
        """Update the timestamp."""
        self.updated = datetime.datetime.now(tz=datetime.timezone.utc)
        self.dump(path)


def hashurl(url: URL) -> str:
    """Return the hashsum for the given URL.

    This function creates a 128-character digest using the BLAKE2b hash
    algorithm.
    """
    data = str(url).encode()
    return hashlib.blake2b(data).hexdigest()


class Backend:
    """Storage backend for repositories."""

    def __init__(self, path: pathlib.Path) -> None:
        """Initialize."""
        self.path = path
        self.path.mkdir(parents=True, exist_ok=True)

    def _getentrypath(self, url: URL) -> pathlib.Path:
        """Return the path to the entry."""
        hash = hashurl(url)
        return self.path / "entries" / hash[:2] / hash

    def get(self, url: URL, provider: str) -> Entry:
        """Retrieve storage for a repository."""
        path = self._getentrypath(url)
        if path.exists():
            entry = Entry.load(path)
            entry.touch(path)
        else:
            path.parent.mkdir(parents=True)
            entry = Entry(path, url, provider)
            entry.dump(path)

        return entry

    def list(self) -> Iterator[Entry]:
        """Return the list of storage entries."""
        root = self.path / "entries"
        for directory in root.iterdir():
            for path in directory.iterdir():
                yield Entry.load(path)

    def clean(self, cutoff: datetime.datetime) -> None:
        """Remove storage entries older than the given timestamp."""
        for entry in self.list():
            if entry.updated < cutoff:
                shutil.rmtree(entry.path)
