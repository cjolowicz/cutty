"""Fetcher for git repositories."""
import pathlib
from typing import Optional

import pygit2
from yarl import URL

from cutty.repositories2.domain.fetchers import fetcher
from cutty.repositories2.domain.matchers import scheme
from cutty.repositories2.domain.revisions import Revision
from cutty.repositories2.domain.stores import defaultstore


@fetcher(
    match=scheme("file", "ftp", "ftps", "git", "http", "https", "ssh"),
    store=lambda url: defaultstore(url).with_suffix(".git"),
)
def gitfetcher(
    url: URL, destination: pathlib.Path, revision: Optional[Revision]
) -> None:
    """Fetch a git repository."""

    def _createremote(
        repository: pygit2.Repository, name: str, url: str
    ) -> pygit2.Remote:
        repository.config[f"remote.{name}.mirror"] = True
        return repository.remotes.create(name, url, "+refs/*:refs/*")

    if destination.exists():
        repository = pygit2.Repository(destination)
        for remote in repository.remotes:
            remote.fetch(prune=pygit2.GIT_FETCH_PRUNE)
    else:
        pygit2.clone_repository(
            str(url), str(destination), bare=True, remote=_createremote
        )
