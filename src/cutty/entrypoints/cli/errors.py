"""Error handling for the command-line interface."""
import pathlib
import shlex
from typing import NoReturn

from cutty.repositories.adapters.fetchers.git import GitFetcherError
from cutty.repositories.adapters.fetchers.mercurial import HgError
from cutty.repositories.adapters.fetchers.mercurial import HgNotFoundError
from cutty.repositories.domain.mounters import UnsupportedRevisionError
from cutty.repositories.domain.registry import UnknownLocationError
from cutty.util.exceptionhandlers import exceptionhandler


def _die(message: str) -> NoReturn:
    raise SystemExit(f"error: {message}")


@exceptionhandler
def _unknownlocation(error: UnknownLocationError) -> NoReturn:
    if isinstance(error.location, pathlib.Path) and not error.location.exists():
        _die(f"no such file or directory: {error.location}")

    _die(f"unknown location {error.location}")


@exceptionhandler
def _unsupportedrevision(error: UnsupportedRevisionError) -> NoReturn:
    _die(f"template does not support revisions, got {error.revision!r}")


@exceptionhandler
def _gitfetcher(error: GitFetcherError) -> NoReturn:
    _die(f"cannot access remote git repository at {error.url}: {error.message}")


@exceptionhandler
def _hgnotfound(error: HgNotFoundError) -> NoReturn:
    _die("cannot locate hg executable on PATH")


@exceptionhandler
def _hg(error: HgError) -> NoReturn:
    command = shlex.join(error.command)
    output = error.stderr if error.stderr else error.stdout
    message = output.splitlines()[0] if output else ""

    _die(f"command {command!r} exited with {error.status}: {message}")


fatal = _unknownlocation >> _unsupportedrevision >> _gitfetcher >> _hgnotfound >> _hg
