"""Providers for git repositories."""
import pathlib
from dataclasses import dataclass
from typing import Optional

import pygit2

from cutty.errors import CuttyError
from cutty.filesystems.adapters.git import GitFilesystem
from cutty.repositories.adapters.fetchers.git import gitfetcher
from cutty.repositories.domain.providers import LocalProvider
from cutty.repositories.domain.providers import RemoteProviderFactory
from cutty.repositories.domain.revisions import Revision


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


def mount(path: pathlib.Path, revision: Optional[Revision]) -> GitFilesystem:
    """Return a filesystem tree for the given revision.

    This function returns the root of a Git filesystem for the given
    revision. If ``revision`` is None, HEAD is used instead.
    """
    if revision is not None:
        try:
            return GitFilesystem(path, revision)
        except KeyError:
            raise RevisionNotFoundError(revision)

    return GitFilesystem(path)


def getrevision(path: pathlib.Path, revision: Optional[Revision]) -> Optional[Revision]:
    """Return the repository revision."""
    if revision is None:
        revision = "HEAD"

    repository = pygit2.Repository(path)
    commit = repository.revparse_single(revision).peel(pygit2.Commit)

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


localgitprovider = LocalProvider(
    "localgit", match=match, mount=mount, getrevision=getrevision
)
gitproviderfactory = RemoteProviderFactory(
    "git", fetch=[gitfetcher], mount=mount, getrevision=getrevision
)
