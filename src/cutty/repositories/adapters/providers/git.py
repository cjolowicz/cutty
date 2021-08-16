"""Providers for git repositories."""
import pathlib
from typing import Optional

import pygit2

from cutty.filesystems.adapters.git import GitFilesystem
from cutty.repositories.adapters.fetchers.git import gitfetcher
from cutty.repositories.domain.providers import localprovider
from cutty.repositories.domain.providers import remoteproviderfactory
from cutty.repositories.domain.revisions import Revision


def match(path: pathlib.Path) -> bool:
    """Return True if the path is a git repository."""
    repository = pygit2.discover_repository(path)
    if repository is None:
        return False

    repositorypath = pathlib.Path(repository)
    return path in (repositorypath, repositorypath.parent)


def mount(path: pathlib.Path, revision: Optional[Revision]) -> GitFilesystem:
    """Return a filesystem tree for the given revision.

    This function returns the root of a Git filesystem for the given
    revision. If ``revision`` is None, HEAD is used instead.
    """
    return GitFilesystem(path, *filter(None, [revision]))


def getrevision(path: pathlib.Path, revision: Optional[Revision]) -> Optional[Revision]:
    """Return the repository revision."""
    if revision is None:
        revision = "HEAD"

    repository = pygit2.Repository(path)
    revision = repository.describe(
        revision,
        describe_strategy=pygit2.GIT_DESCRIBE_TAGS,
        show_commit_oid_as_fallback=True,
    )

    return revision


localgitprovider = localprovider(match=match, mount=mount, getrevision=getrevision)
gitproviderfactory = remoteproviderfactory(fetch=[gitfetcher], mount=mount)
