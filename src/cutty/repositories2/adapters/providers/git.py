"""Providers for git repositories."""
import pathlib
from typing import Optional

import pygit2

from cutty.filesystems.adapters.git import GitFilesystem
from cutty.repositories2.adapters.fetchers.git import gitfetcher
from cutty.repositories2.domain.providers import localprovider
from cutty.repositories2.domain.providers import remoteproviderfactory
from cutty.repositories2.domain.revisions import Revision


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


localgitprovider = localprovider(match=match, mount=mount)
gitproviderfactory = remoteproviderfactory(fetch=[gitfetcher], mount=mount)
