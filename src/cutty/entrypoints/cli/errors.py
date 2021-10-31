"""Error handling for the command-line interface."""
import pathlib
from typing import NoReturn

from cutty.packages.adapters.fetchers.file import FileFetcherError
from cutty.packages.adapters.fetchers.git import GitFetcherError
from cutty.packages.adapters.fetchers.http import HTTPFetcherError
from cutty.packages.adapters.fetchers.mercurial import HgError
from cutty.packages.adapters.fetchers.mercurial import HgNotFoundError
from cutty.packages.adapters.providers.git import RevisionNotFoundError
from cutty.packages.domain.mounters import UnsupportedRevisionError
from cutty.packages.domain.registry import UnknownLocationError
from cutty.packages.domain.repository import ParentRevisionNotImplementedError
from cutty.projects.project import EmptyTemplateError
from cutty.projects.repository import NoUpdateInProgressError
from cutty.services.link import TemplateNotSpecifiedError
from cutty.util.exceptionhandlers import exceptionhandler
from cutty.util.git import MergeConflictError


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
    command = f"hg {error.command[1]}" if len(error.command) > 1 else "hg"

    if message := error.stderr + error.stdout:
        message = message.splitlines()[0]
        message = (
            message.removeprefix("abort: ")
            .removeprefix("error: ")
            .removesuffix(":")
            .strip()
        )
    else:
        message = str(error.status)

    _die(f"{command}: {message}")


@exceptionhandler
def _filefetcher(error: FileFetcherError) -> NoReturn:
    _die(f"cannot fetch template: {error.error}")


@exceptionhandler
def _httpfetcher(error: HTTPFetcherError) -> NoReturn:
    _die(f"cannot fetch template: {error.error}")


@exceptionhandler
def _revisionnotfound(error: RevisionNotFoundError) -> NoReturn:
    _die(f"revision not found: {error.revision}")


@exceptionhandler
def _templatenotspecified(error: TemplateNotSpecifiedError) -> NoReturn:
    _die("template not specified")


@exceptionhandler
def _emptytemplate(error: EmptyTemplateError) -> NoReturn:
    _die("template does not contain project files")


@exceptionhandler
def _noupdateinprogress(error: NoUpdateInProgressError) -> NoReturn:
    _die("no update in progress")


@exceptionhandler
def _mergeconflict(error: MergeConflictError) -> NoReturn:
    _die(f"Merge conflicts: {', '.join(error.paths)}")


@exceptionhandler
def _parentrevisionnotsupported(error: ParentRevisionNotImplementedError) -> NoReturn:
    _die(f"repository {error.name} does not support retrieving the parent revision")


fatal = (
    _unknownlocation
    >> _unsupportedrevision
    >> _gitfetcher
    >> _hgnotfound
    >> _hg
    >> _filefetcher
    >> _httpfetcher
    >> _revisionnotfound
    >> _templatenotspecified
    >> _emptytemplate
    >> _noupdateinprogress
    >> _mergeconflict
    >> _parentrevisionnotsupported
)
