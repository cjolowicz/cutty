"""Provider for Mercurial repositories."""
import pathlib
import shutil
import subprocess  # noqa: S404
from typing import Optional

from cutty.repositories.adapters.fetchers.mercurial import hgfetcher
from cutty.repositories.domain.providers import remoteproviderfactory
from cutty.repositories.domain.revisions import Revision


def getrevision(path: pathlib.Path, revision: Optional[Revision]) -> Optional[Revision]:
    """Return the repository revision."""
    executable = shutil.which("hg")

    def hg(*args: str) -> subprocess.CompletedProcess[str]:
        """Run a hg command."""
        if executable is None:
            raise RuntimeError("cannot locate hg")

        return subprocess.run(  # noqa: S603
            [executable, *args], check=True, capture_output=True, text=True, cwd=path
        )

    if revision is None:
        revision = "."

    result = hg("log", f"--rev={revision}", "--template={node|short}")
    return result.stdout


hgproviderfactory = remoteproviderfactory(fetch=[hgfetcher], getrevision=getrevision)
