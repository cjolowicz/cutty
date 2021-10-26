"""Provider for Mercurial repositories."""
import pathlib
from typing import Optional

from cutty.packages.adapters.fetchers.mercurial import findhg
from cutty.packages.adapters.fetchers.mercurial import hgfetcher
from cutty.packages.domain.providers import _defaultmount
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


hgproviderfactory = RemoteProviderFactory(
    "hg", fetch=[hgfetcher], getrevision=getrevision, mount=_defaultmount
)
