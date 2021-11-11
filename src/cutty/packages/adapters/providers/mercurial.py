"""Provider for Mercurial repositories."""
import datetime
import json
import pathlib
import subprocess  # noqa: S404
import tempfile
from collections.abc import Iterator
from typing import Optional

from cutty.compat.contextlib import contextmanager
from cutty.filesystems.adapters.disk import DiskFilesystem
from cutty.filesystems.domain.filesystem import Filesystem
from cutty.packages.adapters.fetchers.mercurial import findhg
from cutty.packages.adapters.fetchers.mercurial import hgfetcher
from cutty.packages.domain.loader import PackageRepositoryLoader
from cutty.packages.domain.package import Author
from cutty.packages.domain.package import Commit
from cutty.packages.domain.providers import RemoteProviderFactory
from cutty.packages.domain.repository import DefaultPackageRepository
from cutty.packages.domain.revisions import Revision


class MercurialPackageRepository(DefaultPackageRepository):
    """Mercurial package repository."""

    def __init__(self, name: str, path: pathlib.Path) -> None:
        """Initialize."""
        super().__init__(name, path)

        self._hg = findhg()

    def hg(self, *args: str) -> subprocess.CompletedProcess[str]:
        """Invoke hg."""
        return self._hg(*args, cwd=self.path)

    @contextmanager
    def mount(self, revision: Optional[Revision]) -> Iterator[Filesystem]:
        """Mount an archive of the revision as a disk filesystem."""
        with tempfile.TemporaryDirectory() as directory:
            options = ["--rev", revision] if revision is not None else []
            self.hg("archive", *options, directory)

            yield DiskFilesystem(pathlib.Path(directory))

    def lookup(self, revision: Optional[Revision]) -> Optional[Commit]:
        """Look up the commit metadata for the given revision."""
        template = """
        json(
            dict(
                id=node,
                revision=ifeq(latesttagdistance, 0, join(latesttag, ":"), short(node)),
                message=desc,
                name=person(author),
                email=email(author),
                date=date(date, "%Y-%m-%dT%H:%M:%S%z")))
        """
        text = self.getmetadata(revision, template)
        data = json.loads(text)

        return Commit(
            data["id"],
            data["revision"],
            data["message"],
            Author(data["name"], data["email"]),
            datetime.datetime.strptime(data["date"], "%Y-%m-%dT%H:%M:%S%z"),
        )

    def getmetadata(self, revision: Optional[Revision], template: str) -> str:
        """Return commit metadata."""
        if revision is None:
            revision = "."

        result = self.hg("log", f"--rev={revision}", f"--template={{{template}}}")
        return result.stdout

    def getparentrevision(self, revision: Optional[Revision]) -> Optional[Revision]:
        """Return the parent revision, if any."""
        if revision is None:
            revision = "."

        return self.getmetadata(f"p1({revision})", "node") or None


class MercurialRepositoryLoader(PackageRepositoryLoader):
    """Mercurial repository loader."""

    def load(self, name: str, path: pathlib.Path) -> MercurialPackageRepository:
        """Load a package repository."""
        return MercurialPackageRepository(name, path)


hgproviderfactory = RemoteProviderFactory(
    "hg", fetch=[hgfetcher], loader=MercurialRepositoryLoader()
)
