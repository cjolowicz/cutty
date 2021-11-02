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
from cutty.packages.domain.providers import LocalProvider
from cutty.packages.domain.providers import RemoteProviderFactory
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


def getcommit(path: pathlib.Path, revision: Optional[Revision]) -> Optional[Revision]:
    """Return the commit identifier."""
    repository = pygit2.Repository(path)
    commit = _getcommit(repository, revision)
    return str(commit.id)


def getrevision(path: pathlib.Path, revision: Optional[Revision]) -> Optional[Revision]:
    """Return the package revision."""
    repository = pygit2.Repository(path)
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


def getparentrevision(
    path: pathlib.Path, revision: Optional[Revision]
) -> Optional[Revision]:
    """Return the parent revision, if any."""
    repository = pygit2.Repository(path)

    if revision is None:
        revision = "HEAD"

    try:
        commit = repository.revparse_single(revision).peel(pygit2.Commit)
    except KeyError:
        raise RevisionNotFoundError(revision)

    if parents := commit.parents:
        [parent] = parents

        return str(parent.id)

    return None


def getmessage(path: pathlib.Path, revision: Optional[Revision]) -> Optional[str]:
    """Return the commit message."""
    if revision is None:
        revision = "HEAD"

    repository = pygit2.Repository(path)

    try:
        commit = repository.revparse_single(revision).peel(pygit2.Commit)
    except KeyError:  # pragma: no cover
        raise RevisionNotFoundError(revision)

    message: str = commit.message
    return message


localgitprovider = LocalProvider(
    "localgit",
    match=match,
    mount=mount,
    getcommit=getcommit,
    getrevision=getrevision,
    getparentrevision=getparentrevision,
    getmessage=getmessage,
)

gitproviderfactory = RemoteProviderFactory(
    "git",
    fetch=[gitfetcher],
    mount=mount,
    getcommit=getcommit,
    getrevision=getrevision,
    getparentrevision=getparentrevision,
    getmessage=getmessage,
)
