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
from cutty.packages.domain.revisions import Revision


def getrevision(path: pathlib.Path, revision: Optional[Revision]) -> Optional[Revision]:
    """Return the package revision."""
    hg = findhg()

    if revision is None:
        revision = "."

    result = hg(
        "log",
        f"--rev={revision}",
        "--template={ifeq(latesttagdistance, 0, latesttag, short(node))}",
        cwd=path,
    )
    return result.stdout


@contextmanager
def mount(path: pathlib.Path, revision: Optional[Revision]) -> Iterator[Filesystem]:
    """Mount an archive of the revision as a disk filesystem."""
    hg = findhg()

    with tempfile.TemporaryDirectory() as directory:
        options = ["--rev", revision] if revision is not None else []
        hg("archive", *options, directory, cwd=path)

        yield DiskFilesystem(pathlib.Path(directory))


def getparentrevision(
    path: pathlib.Path, revision: Optional[Revision]
) -> Optional[Revision]:
    """Return the parent revision, if any."""
    if revision is None:
        revision = "."

    hg = findhg()

    result = hg("log", f"--rev=p1({revision})", "--template={node}", cwd=path)

    return result.stdout or None


hgproviderfactory = RemoteProviderFactory(
    "hg",
    fetch=[hgfetcher],
    getrevision=getrevision,
    getparentrevision=getparentrevision,
    mount=mount,
)
