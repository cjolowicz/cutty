"""Providers for git repositories."""
import pathlib
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Optional

import pygit2

from cutty.compat.contextlib import contextmanager
from cutty.errors import CuttyError
from cutty.filesystems.adapters.git import GitFilesystem
from cutty.packages.adapters.fetchers.git import gitfetcher
from cutty.packages.domain.loader import PackageRepositoryLoader
from cutty.packages.domain.package import Author
from cutty.packages.domain.package import Commit
from cutty.packages.domain.providers import LocalProvider
from cutty.packages.domain.providers import RemoteProviderFactory
from cutty.packages.domain.repository import DefaultPackageRepository
from cutty.packages.domain.repository import PackageRepository
from cutty.packages.domain.revisions import Revision
from cutty.util.time import asdatetime


@dataclass
class RevisionNotFoundError(CuttyError):
    """The specified revision does not exist in the repository."""

    revision: Revision


class GitPackageRepository(DefaultPackageRepository):
    """Git package repository."""

    def __init__(self, name: str, path: pathlib.Path) -> None:
        """Initialize."""
        super().__init__(name, path)

        self.repository = pygit2.Repository(path)

    @contextmanager
    def mount(self, revision: Optional[Revision]) -> Iterator[GitFilesystem]:
        """Return a filesystem tree for the given revision.

        This function returns the root of a Git filesystem for the given
        revision. If ``revision`` is None, HEAD is used instead.
        """
        if revision is not None:
            yield GitFilesystem(self.path, revision)
        else:
            yield GitFilesystem(self.path)

    def lookup(self, revision: Optional[Revision]) -> Optional[Commit]:
        """Look up the commit metadata for the given revision."""
        commit = self._lookup(revision)
        author = Author(commit.author.name, commit.author.email)
        date = asdatetime(commit.author.time, offset=commit.author.offset)

        return Commit(
            str(commit.id), self.describe(commit), commit.message, author, date
        )

    def _lookup(self, revision: Optional[Revision]) -> pygit2.Commit:
        """Return the commit object."""
        if revision is None:
            revision = "HEAD"

        try:
            return self.repository.revparse_single(revision).peel(pygit2.Commit)
        except KeyError:
            raise RevisionNotFoundError(revision)

    def describe(self, commit: pygit2.Commit) -> str:
        """Return the resolved revision."""
        revision: str

        try:
            revision = self.repository.describe(
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
        commit = self._lookup(revision)

        if parents := commit.parents:
            [parent] = parents

            return str(parent.id)

        return None


class GitRepositoryLoader(PackageRepositoryLoader):
    """Git repository loader."""

    def load(self, name: str, path: pathlib.Path) -> PackageRepository:
        """Load a package repository."""
        return GitPackageRepository(name, path)


def match(path: pathlib.Path) -> bool:
    """Return True if the path is a git repository."""
    repository = pygit2.discover_repository(path)
    if repository is None:
        return False

    repositorypath = pathlib.Path(repository)
    return path in (repositorypath, repositorypath.parent)


localgitprovider = LocalProvider("localgit", match=match, loader=GitRepositoryLoader())
gitproviderfactory = RemoteProviderFactory(
    "git", fetch=[gitfetcher], loader=GitRepositoryLoader()
)
