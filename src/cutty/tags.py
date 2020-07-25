"""Determining the versions tagged in a Git repository."""
from __future__ import annotations

import contextlib
from dataclasses import dataclass
from typing import Iterator
from typing import Optional

from packaging.version import InvalidVersion
from packaging.version import Version

from . import git


@dataclass
class VersionTag:
    """Git tag for a version according to PEP 440."""

    name: str
    version: Version

    @classmethod
    def create(cls, name: str) -> VersionTag:
        """Parse the tag name as a PEP 440 version."""
        version = Version(name[1:] if name.startswith("v") else name)
        return cls(name, version)


def load(repository: git.Repository) -> Iterator[VersionTag]:
    """Load versions tagged in the repository."""
    for tag in repository.tags():
        with contextlib.suppress(InvalidVersion):
            yield VersionTag.create(tag)


def find_latest(repository: git.Repository) -> Optional[str]:
    """Return the Git tag for the latest version."""
    tags = list(load(repository))

    if tags:
        latest = max(tags, key=lambda tag: tag.version)
        return latest.name

    return None
