"""Fetch a package from the filesystem."""
import pathlib
import shutil
from dataclasses import dataclass
from typing import NoReturn

from yarl import URL

from cutty.errors import CuttyError
from cutty.packages.domain.fetchers import fetcher
from cutty.packages.domain.locations import aspath
from cutty.packages.domain.matchers import scheme
from cutty.util.exceptionhandlers import exceptionhandler


@dataclass
class FileFetcherError(CuttyError):
    """The file or directory could not be fetched."""

    error: OSError


@exceptionhandler
def _errorhandler(error: OSError) -> NoReturn:
    raise FileFetcherError(error)


@fetcher(match=scheme("file"))
@_errorhandler
def filefetcher(url: URL, destination: pathlib.Path) -> None:
    """Copy a file or directory."""
    if destination.is_dir():
        shutil.rmtree(destination)
    elif destination.exists():
        destination.unlink()

    source = aspath(url)

    if source.is_dir():
        shutil.copytree(source, destination, symlinks=True)
    else:
        shutil.copy2(source, destination, follow_symlinks=False)
