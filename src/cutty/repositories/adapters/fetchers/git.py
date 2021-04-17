"""Fetcher for git repositories."""
import contextlib
import pathlib
from typing import Optional

import pygit2
from yarl import URL

from cutty.repositories.domain.fetchers import fetcher
from cutty.repositories.domain.matchers import scheme
from cutty.repositories.domain.revisions import Revision
from cutty.repositories.domain.stores import defaultstore


def _fix_repository_head(repository: pygit2.Repository) -> pygit2.Reference:
    """Work around a bug in libgit2 resulting in a bogus HEAD reference.

    Cloning with a remote callback results in HEAD pointing to the user's
    `init.defaultBranch` instead of the default branch of the cloned repository.
    """
    # https://github.com/libgit2/pygit2/issues/1073
    head = repository.references["HEAD"]

    with contextlib.suppress(KeyError):
        return head.resolve()

    for branch in ["main", "master"]:
        ref = f"refs/heads/{branch}"
        if ref in repository.references:
            head.set_target(ref, message="repair broken HEAD after clone")
            break

    return head.resolve()


@fetcher(
    match=scheme("file", "ftp", "ftps", "git", "http", "https", "ssh"),
    store=lambda url: defaultstore(url).with_suffix(".git"),
)
def gitfetcher(
    url: URL, destination: pathlib.Path, revision: Optional[Revision]
) -> None:
    """Fetch a git repository."""

    def _createremote(
        repository: pygit2.Repository, name: bytes, url: bytes
    ) -> pygit2.Remote:
        name_ = name.decode()
        repository.config[f"remote.{name_}.mirror"] = True
        return repository.remotes.create(name, url, "+refs/*:refs/*")

    if destination.exists():
        repository = pygit2.Repository(destination)
        for remote in repository.remotes:
            remote.fetch(prune=pygit2.GIT_FETCH_PRUNE)
    else:
        _fix_repository_head(
            pygit2.clone_repository(
                str(url), str(destination), bare=True, remote=_createremote
            )
        )
