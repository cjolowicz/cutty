"""Provider for Mercurial repositories."""
import pathlib
import tempfile
from collections.abc import Iterator
from typing import Optional

from cutty.compat.contextlib import contextmanager
from cutty.filesystems.adapters.disk import DiskFilesystem
from cutty.filesystems.domain.filesystem import Filesystem
from cutty.packages.adapters.fetchers.mercurial import findhg
from cutty.packages.adapters.fetchers.mercurial import hgfetcher
from cutty.packages.domain.loader import PackageRepositoryLoader
from cutty.packages.domain.providers import RemoteProviderFactory
from cutty.packages.domain.repository import DefaultPackageRepository
from cutty.packages.domain.revisions import Revision


class MercurialPackageRepository(DefaultPackageRepository):
    """Mercurial package repository."""

    @contextmanager
    def mount(self, revision: Optional[Revision]) -> Iterator[Filesystem]:
        """Mount an archive of the revision as a disk filesystem."""
        hg = findhg()

        with tempfile.TemporaryDirectory() as directory:
            options = ["--rev", revision] if revision is not None else []
            hg("archive", *options, directory, cwd=self.path)

            yield DiskFilesystem(pathlib.Path(directory))

    def getmetadata(self, revision: Optional[Revision], template: str) -> Optional[str]:
        """Return commit metadata."""
        hg = findhg()

        if revision is None:
            revision = "."

        result = hg(
            "log", f"--rev={revision}", f"--template={{{template}}}", cwd=self.path
        )
        return result.stdout

    def getcommit(self, revision: Optional[Revision]) -> Optional[Revision]:
        """Return the commit identifier."""
        return self.getmetadata(revision, "node")

    def getrevision(self, revision: Optional[Revision]) -> Optional[Revision]:
        """Return the package revision."""
        return self.getmetadata(
            revision, "ifeq(latesttagdistance, 0, latesttag, short(node))"
        )

    def getparentrevision(self, revision: Optional[Revision]) -> Optional[Revision]:
        """Return the parent revision, if any."""
        if revision is None:
            revision = "."

        return self.getmetadata(f"p1({revision})", "node") or None

    def getmessage(self, revision: Optional[Revision]) -> Optional[str]:
        """Return the commit message."""
        return self.getmetadata(revision, "desc")


class MercurialRepositoryLoader(PackageRepositoryLoader):
    """Mercurial repository loader."""

    def load(self, name: str, path: pathlib.Path) -> MercurialPackageRepository:
        """Load a package repository."""
        return MercurialPackageRepository(name, path)


hgproviderfactory = RemoteProviderFactory(
    "hg", fetch=[hgfetcher], loader=MercurialRepositoryLoader()
)
