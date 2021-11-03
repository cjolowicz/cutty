"""Providers for git repositories."""
import pathlib
from collections.abc import Iterator
from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Optional

import pygit2

from cutty.compat.contextlib import contextmanager
from cutty.errors import CuttyError
from cutty.filesystems.adapters.git import GitFilesystem
from cutty.filesystems.domain.filesystem import Filesystem
from cutty.packages.adapters.fetchers.git import gitfetcher
from cutty.packages.domain.providers import LocalProvider
from cutty.packages.domain.providers import RemoteProviderFactory
from cutty.packages.domain.repository import DefaultPackageRepository
from cutty.packages.domain.repository import PackageRepository
from cutty.packages.domain.repository import PackageRepositoryProvider
from cutty.packages.domain.revisions import Revision


def match(path: pathlib.Path) -> bool:
    """Return True if the path is a git repository."""
    repository = pygit2.discover_repository(path)
    if repository is None:
        return False

    repositorypath = pathlib.Path(repository)
    return path in (repositorypath, repositorypath.parent)


@dataclass
class RevisionNotFoundError(CuttyError):
    """The specified revision does not exist in the repository."""

    revision: Revision


@contextmanager
def mount(path: pathlib.Path, revision: Optional[Revision]) -> Iterator[GitFilesystem]:
    """Return a filesystem tree for the given revision.

    This function returns the root of a Git filesystem for the given
    revision. If ``revision`` is None, HEAD is used instead.
    """
    if revision is not None:
        yield GitFilesystem(path, revision)
    else:
        yield GitFilesystem(path)


def _getcommit(
    repository: pygit2.Repository, revision: Optional[Revision]
) -> pygit2.Commit:
    """Return the commit object."""
    if revision is None:
        revision = "HEAD"

    try:
        return repository.revparse_single(revision).peel(pygit2.Commit)
    except KeyError:
        raise RevisionNotFoundError(revision)


def getparentrevision(
    path: pathlib.Path, revision: Optional[Revision]
) -> Optional[Revision]:
    """Return the parent revision, if any."""
    repository = pygit2.Repository(path)
    commit = _getcommit(repository, revision)

    if parents := commit.parents:
        [parent] = parents

        return str(parent.id)

    return None


def getmessage(path: pathlib.Path, revision: Optional[Revision]) -> Optional[str]:
    """Return the commit message."""
    repository = pygit2.Repository(path)
    commit = _getcommit(repository, revision)
    message: str = commit.message

    return message


class GitPackageRepository(DefaultPackageRepository):
    """Git package repository."""

    def __init__(self, name: str, path: pathlib.Path) -> None:
        """Initialize."""
        super().__init__(name, path)

    def mount(self, revision: Optional[Revision]) -> AbstractContextManager[Filesystem]:
        """Mount the package filesystem."""
        return mount(self.path, revision)

    def getcommit(self, revision: Optional[Revision]) -> Optional[Revision]:
        """Return the commit identifier."""
        repository = pygit2.Repository(self.path)
        commit = _getcommit(repository, revision)
        return str(commit.id)

    def getrevision(self, revision: Optional[Revision]) -> Optional[Revision]:
        """Return the resolved revision."""
        repository = pygit2.Repository(self.path)
        commit = _getcommit(repository, revision)

        try:
            revision = repository.describe(
                commit,
                describe_strategy=pygit2.GIT_DESCRIBE_TAGS,
                max_candidates_tags=0,
                show_commit_oid_as_fallback=True,
            )
        except KeyError:
            # Emulate `show_commit_oid_as_fallback` when no tag matches exactly,
            # which results in GIT_ENOTFOUND ("cannot describe - no tag exactly
            # matches '...'").
            revision = commit.short_id

        return revision

    def getparentrevision(self, revision: Optional[Revision]) -> Optional[Revision]:
        """Return the parent revision, if any."""
        return getparentrevision(self.path, revision)

    def getmessage(self, revision: Optional[Revision]) -> Optional[str]:
        """Return the commit message."""
        return getmessage(self.path, revision)


class GitProvider(PackageRepositoryProvider):
    """Git repository provider."""

    def provide(self, name: str, path: pathlib.Path) -> PackageRepository:
        """Load a package repository."""
        return GitPackageRepository(name, path)


localgitprovider = LocalProvider("localgit", match=match, provider=GitProvider())
gitproviderfactory = RemoteProviderFactory(
    "git", fetch=[gitfetcher], provider=GitProvider()
)
