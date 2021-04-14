"""Determining the versions tagged in a Git repository."""
from __future__ import annotations

import contextlib
from dataclasses import dataclass
from typing import Iterator
from typing import Optional

import packaging.version

from . import exceptions
from . import git


@dataclass
class Tag:
    """Git tag for a version according to PEP 440."""

    name: str
    version: packaging.version.Version

    @classmethod
    def create(cls, name: str) -> Tag:
        """Parse the tag name as a PEP 440 version."""
        version = packaging.version.Version(name[1:] if name.startswith("v") else name)
        return cls(name, version)


def load_tags(repository: git.Repository) -> Iterator[Tag]:
    """Load versions tagged in the repository."""
    for tag in repository.tags():
        with contextlib.suppress(packaging.version.InvalidVersion):
            yield Tag.create(tag)


def find_latest_tag(repository: git.Repository) -> Optional[Tag]:
    """Return the Git tag for the latest version."""
    tags = load_tags(repository)

    with contextlib.suppress(ValueError):
        return max(tags, key=lambda tag: tag.version)

    return None


@dataclass
class Version:
    """Template version."""

    name: str
    sha1: str

    @classmethod
    def get(
        cls, repository: git.Repository, *, revision: Optional[str] = None
    ) -> Version:
        """Return the latest version, unless specified otherwise."""
        if revision is not None:
            return find_version(repository, revision)

        version = find_latest_version(repository)
        if version is not None:
            return version

        return find_version(repository, "HEAD")


def find_version(repository: git.Repository, revision: str) -> Version:
    """Return the tag or short SHA-1 for the revision."""
    with exceptions.InvalidRevision(revision):
        sha1 = repository.rev_parse(revision, verify=True)

    with contextlib.suppress(git.Error, packaging.version.InvalidVersion):
        tagname = repository.describe(revision, tags=True, exact_match=True)
        tag = Tag.create(tagname)
        return Version(tag.name, sha1)

    name = repository.rev_parse(revision, short=True)
    return Version(name, sha1)


def find_latest_version(repository: git.Repository) -> Optional[Version]:
    """Return the latest version tagged in the repository, if any."""
    tag = find_latest_tag(repository)

    if tag is None:
        return None

    sha1 = repository.rev_parse(tag.name, verify=True)
    return Version(tag.name, sha1)
