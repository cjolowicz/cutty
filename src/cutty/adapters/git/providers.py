"""Git-based provider."""
import pathlib
from urllib.parse import urlparse

import pygit2

from cutty.adapters.disk.hooks import resolve
from cutty.filesystem.path import Path


def _createremote(repository: pygit2.Repository, name: str, url: str) -> pygit2.Remote:
    repository.config[f"remote.{name}.mirror"] = True
    return repository.remotes.create(name, url, "+refs/*:refs/*")


def _getrepositoryname(url: str) -> str:
    path = urlparse(url).path
    name = pathlib.PurePosixPath(path).stem
    return f"{name}.git"


def gitdownload(url: str, path: Path) -> None:
    """Download the URL to the given path."""
    location = resolve(path) / _getrepositoryname(url)
    pygit2.clone_repository(url, location, bare=True, remote=_createremote)
