"""Fetcher for Mercurial repositories."""
import pathlib
import shutil
import subprocess  # noqa: S404
from typing import Optional

from yarl import URL

from cutty.repositories.domain.fetchers import fetcher
from cutty.repositories.domain.matchers import scheme
from cutty.repositories.domain.revisions import Revision


@fetcher(match=scheme("file", "http", "https", "ssh"))
def hgfetcher(
    url: URL, destination: pathlib.Path, revision: Optional[Revision]
) -> None:
    """Fetch the repository using hg."""
    executable = shutil.which("hg")

    def hg(
        *args: str, cwd: Optional[pathlib.Path] = None
    ) -> subprocess.CompletedProcess[str]:
        """Run a hg command."""
        if executable is None:
            raise RuntimeError("cannot locate hg")

        return subprocess.run(  # noqa: S603
            [executable, *args], check=True, capture_output=True, text=True, cwd=cwd
        )

    if destination.exists():
        hg("pull", cwd=destination)
    else:
        hg("clone", "--noupdate", str(url), str(destination))

    options = ["--rev", revision] if revision is not None else []
    hg("update", *options, cwd=destination)
