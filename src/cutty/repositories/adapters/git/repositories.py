"""Git repository."""
import pathlib
from typing import Optional

import pygit2
from yarl import URL

from cutty.filesystem.git import GitFilesystem
from cutty.filesystem.path import Path
from cutty.repositories.domain.repositories import Repository


class GitRepository(Repository):
    """Git repository provider."""

    name: str = "git"
    schemes = {"file", "ftp", "ftps", "git", "http", "https", "ssh"}

    @property
    def repositorypath(self) -> pathlib.Path:
        """Return the directory where the repository is stored."""
        name = pathlib.PurePosixPath(self.url.path).stem
        return self.path / f"{name}.git"

    @classmethod
    def matches(cls, url: URL) -> bool:
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
        return not url.scheme or url.scheme in cls.schemes

    def exists(self) -> bool:
        """Return True if the repository exists."""
        return self.repositorypath.exists()

    def download(self) -> None:
        """Download the repository to the given path.

        This function clones the URL to a bare repository, and configures
        the remote to mirror all refs.
        """

        def _createremote(
            repository: pygit2.Repository, name: str, url: str
        ) -> pygit2.Remote:
            repository.config[f"remote.{name}.mirror"] = True
            return repository.remotes.create(name, url, "+refs/*:refs/*")

        pygit2.clone_repository(
            self.url, self.repositorypath, bare=True, remote=_createremote
        )

    def update(self) -> None:
        """Update the repository at the given path.

        This function fetches the remote and prunes stale branches.
        """
        repository = pygit2.Repository(self.repositorypath)
        for remote in repository.remotes:
            remote.fetch(prune=pygit2.GIT_FETCH_PRUNE)

    def resolve(self, revision: Optional[str]) -> Path:
        """Return a filesystem tree for the given revision.

        This function returns the root of a Git filesystem for the given
        revision. If ``revision`` is None, HEAD is used instead.
        """
        filesystem = GitFilesystem(self.repositorypath, *filter(None, [revision]))
        return Path(filesystem=filesystem)
