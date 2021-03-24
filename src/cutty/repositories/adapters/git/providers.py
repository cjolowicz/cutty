"""Git-based repository provider."""
import pathlib
from typing import Optional

import pygit2
from yarl import URL

from cutty.filesystem.git import GitFilesystem
from cutty.filesystem.path import Path
from cutty.repositories.domain.providers import Provider


def getrepositorypath(url: URL, path: pathlib.Path) -> pathlib.Path:
    """Return the directory where the repository is stored."""
    name = pathlib.PurePosixPath(url.path).stem
    return path / f"{name}.git"


class GitProvider(Provider):
    """Git repository provider."""

    name: str = "git"
    schemes = {"file", "ftp", "ftps", "git", "http", "https", "ssh"}

    def matches(self, url: URL) -> bool:
        """Return True if the provider handles the given URL.

        This provider handles the following URLs (see git-clone(1)):

          - /path/to/repo.git/
          - file:///path/to/repo.git/
          - ssh://[user@]host.xz[:port]/path/to/repo.git/
          - git://host.xz[:port]/path/to/repo.git/
          - http[s]://host.xz[:port]/path/to/repo.git/
          - ftp[s]://host.xz[:port]/path/to/repo.git/

        The following shorthand for the ssh protocol is *not* supported (git
        recognizes this syntax if there are no slashes before the first colon):

          - [user@]host.xz:path/to/repo.git/
        """
        return not url.scheme or url.scheme in self.schemes

    def download(self, url: URL, path: pathlib.Path) -> None:
        """Download the repository to the given path.

        This function clones the URL to a bare repository, and configures
        the remote to mirror all refs.
        """

        def _createremote(
            repository: pygit2.Repository, name: str, url: str
        ) -> pygit2.Remote:
            repository.config[f"remote.{name}.mirror"] = True
            return repository.remotes.create(name, url, "+refs/*:refs/*")

        path = getrepositorypath(url, path)
        pygit2.clone_repository(url, path, bare=True, remote=_createremote)

    def update(self, url: URL, path: pathlib.Path) -> None:
        """Update the repository at the given path.

        This function fetches the remote and prunes stale branches.
        """
        path = getrepositorypath(url, path)
        repository = pygit2.Repository(path)
        for remote in repository.remotes:
            remote.fetch(prune=pygit2.GIT_FETCH_PRUNE)

    def resolve(self, url: URL, path: pathlib.Path, revision: Optional[str]) -> Path:
        """Return a filesystem tree for the given revision.

        This function returns the root of a Git filesystem for the given
        revision. If ``revision`` is None, HEAD is used instead.
        """
        path = getrepositorypath(url, path)
        filesystem = GitFilesystem(path, *filter(None, [revision]))
        return Path(filesystem=filesystem)
