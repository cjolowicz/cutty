"""Mercurial repository."""
from __future__ import annotations

import pathlib
import shutil
import subprocess  # noqa: S404
from typing import Optional

from yarl import URL

from cutty.filesystems.adapters.disk import DiskFilesystem
from cutty.repositories.domain.repositories import Repository


class MercurialRepository(Repository):
    """Git repository."""

    type: str = "hg"
    schemes = {"file", "http", "https", "ssh"}

    @property
    def repositorypath(self) -> pathlib.Path:
        """Return the directory where the repository is stored."""
        name = pathlib.PurePosixPath(self.url.path).name
        return self.path / name

    def run(
        self, *args: str, cwd: Optional[pathlib.Path] = None
    ) -> subprocess.CompletedProcess[str]:
        """Run a hg(1) command."""
        hg = shutil.which("hg")
        assert hg is not None  # noqa: S101
        return subprocess.run(  # noqa: S603
            [hg, *args], check=True, capture_output=True, text=True, cwd=cwd
        )

    @classmethod
    def supports(cls, url: URL) -> bool:
        """Return True if the implementation supports the given URL.

        This implementation handles the following URLs (see ``hg help urls``):

          - local/filesystem/path
          - file://local/filesystem/path
          - http://[user[:pass]@]host[:port]/[path]
          - https://[user[:pass]@]host[:port]/[path]
          - ssh://[user@]host[:port]/[path]
        """
        if shutil.which("hg") is None:
            return False

        if not url.scheme:
            hgrc = pathlib.Path(url.path) / ".hg" / "hgrc"
            return hgrc.is_file()

        return url.scheme in cls.schemes

    def exists(self) -> bool:
        """Return True if the repository exists."""
        return self.repositorypath.exists()

    def download(self) -> None:
        """Download the repository to the given path.

        This function clones the URL using hg(1).
        """
        self.run("clone", str(self.url), str(self.repositorypath))

    def update(self) -> None:
        """Update the repository at the given path.

        This function pulls changes from the default source.
        """
        self.run("pull", cwd=self.repositorypath)

    def resolve(self, revision: Optional[str]) -> DiskFilesystem:
        """Return a filesystem tree for the given revision.

        This function updates the repository to the given revision, and returns
        a disk filesystem rooted in the working directory. If ``revision`` is
        None, the default branch is used instead.
        """
        options = ["--rev", revision] if revision is not None else []
        self.run("update", *options, cwd=self.repositorypath)
        return DiskFilesystem(self.repositorypath)
