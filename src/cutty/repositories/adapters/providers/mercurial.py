"""Provider for Mercurial repositories."""
import pathlib
from typing import Optional

from cutty.repositories.adapters.fetchers.mercurial import findhg
from cutty.repositories.adapters.fetchers.mercurial import hgfetcher
from cutty.repositories.domain.providers import RemoteProviderFactory
from cutty.repositories.domain.revisions import Revision


def getrevision(path: pathlib.Path, revision: Optional[Revision]) -> Optional[Revision]:
    """Return the repository revision."""
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


hgproviderfactory = RemoteProviderFactory(
    "hg", fetch=[hgfetcher], getrevision=getrevision
)
