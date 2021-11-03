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
from cutty.packages.domain.providers import RemoteProviderFactory
from cutty.packages.domain.repository import DefaultPackageRepository
from cutty.packages.domain.repository import PackageRepositoryProvider
from cutty.packages.domain.revisions import Revision


def getmetadata(
    path: pathlib.Path, revision: Optional[Revision], template: str
) -> Optional[str]:
    """Return commit metadata."""
    hg = findhg()

    if revision is None:
        revision = "."

    result = hg("log", f"--rev={revision}", f"--template={{{template}}}", cwd=path)
    return result.stdout


def getcommit(path: pathlib.Path, revision: Optional[Revision]) -> Optional[Revision]:
    """Return the commit identifier."""
    return getmetadata(path, revision, "node")


def getrevision(path: pathlib.Path, revision: Optional[Revision]) -> Optional[Revision]:
    """Return the package revision."""
    return getmetadata(
        path, revision, "ifeq(latesttagdistance, 0, latesttag, short(node))"
    )


def getparentrevision(
    path: pathlib.Path, revision: Optional[Revision]
) -> Optional[Revision]:
    """Return the parent revision, if any."""
    if revision is None:
        revision = "."

    return getmetadata(path, f"p1({revision})", "node") or None


def getmessage(path: pathlib.Path, revision: Optional[Revision]) -> Optional[str]:
    """Return the commit message."""
    return getmetadata(path, revision, "desc")


@contextmanager
def mount(path: pathlib.Path, revision: Optional[Revision]) -> Iterator[Filesystem]:
    """Mount an archive of the revision as a disk filesystem."""
    hg = findhg()

    with tempfile.TemporaryDirectory() as directory:
        options = ["--rev", revision] if revision is not None else []
        hg("archive", *options, directory, cwd=path)

        yield DiskFilesystem(pathlib.Path(directory))


class MercurialProvider(PackageRepositoryProvider):
    """Mercurial repository provider."""

    def provide(self, name: str, path: pathlib.Path) -> DefaultPackageRepository:
        """Load a package repository."""
        return DefaultPackageRepository(
            name,
            path,
            getcommit=getcommit,
            getrevision=getrevision,
            getparentrevision=getparentrevision,
            getmessage=getmessage,
            mount=mount,
        )


hgproviderfactory = RemoteProviderFactory(
    "hg", fetch=[hgfetcher], provider=MercurialProvider()
)
