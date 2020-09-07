"""Determining the versions tagged in a Git repository."""
from __future__ import annotations

import contextlib
from dataclasses import dataclass
from typing import Iterator
from typing import Optional

from packaging.version import InvalidVersion
from packaging.version import Version

from .common import git


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


def describe(repository: git.Repository, *, ref: str = "HEAD") -> str:
    """Return the version tag for HEAD, falling back to the short SHA-1."""
    with contextlib.suppress(git.Error, InvalidVersion):
        tag = repository.describe(ref, tags=True, exact=True)
        return VersionTag.create(tag).name
    return repository.rev_parse(ref, short=True)
