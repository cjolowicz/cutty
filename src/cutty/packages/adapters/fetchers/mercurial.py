"""Fetcher for Mercurial repositories."""
import os
import pathlib
import shutil
import subprocess  # noqa: S404
from dataclasses import dataclass
from typing import Optional
from typing import Protocol

from yarl import URL

from cutty.errors import CuttyError
from cutty.packages.domain.fetchers import fetcher
from cutty.packages.domain.matchers import scheme


class HgNotFoundError(CuttyError):
    """Cannot locate the ``hg`` executable."""


@dataclass
class HgError(CuttyError):
    """Mercurial exited with a non-zero status code."""

    command: tuple[str, ...]
    stdout: str
    stderr: str
    status: int
    cwd: Optional[pathlib.Path]


class Hg(Protocol):
    """Protocol for the hg command."""

    def __call__(
        self, *args: str, cwd: Optional[pathlib.Path] = None
    ) -> subprocess.CompletedProcess[str]:
        """Invoke hg."""


def findhg(env: Optional[dict[str, str]] = None) -> Hg:
    """Return a function for running hg commands."""
    if not (path := shutil.which("hg")):
        raise HgNotFoundError()

    executable = path

    def hg(
        *args: str, cwd: Optional[pathlib.Path] = None
    ) -> subprocess.CompletedProcess[str]:
        """Run a hg command."""
        _env = os.environ | env if env is not None else None

        try:
            return subprocess.run(  # noqa: S603
                [executable, *args],
                check=True,
                capture_output=True,
                text=True,
                cwd=cwd,
                env=_env,
            )
        except subprocess.CalledProcessError as error:
            raise HgError(
                (executable, *args), error.stdout, error.stderr, error.returncode, cwd
            )

    return hg


@fetcher(match=scheme("file", "http", "https", "ssh"))
def hgfetcher(url: URL, destination: pathlib.Path) -> None:
    """Fetch the package using hg."""
    hg = findhg()

    if destination.exists():
        hg("pull", cwd=destination)
    else:
        hg("clone", str(url), str(destination))
