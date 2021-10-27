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
from cutty.packages.domain.fetchers import Fetcher2
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


hgproviderfactory = RemoteProviderFactory(
    "hg", fetch2=[Fetcher2(hgfetcher)], getrevision=getrevision, mount=mount
)
