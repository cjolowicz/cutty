"""Git-based provider."""
import pygit2

from cutty.adapters.disk.hooks import resolve
from cutty.filesystem.path import Path


def _createremote(repository: pygit2.Repository, name: str, url: str) -> pygit2.Remote:
    repository.config[f"remote.{name}.mirror"] = True
    return repository.remotes.create(name, url, "+refs/*:refs/*")


def gitdownload(url: str, path: Path) -> None:
    """Download the URL to the given path."""
    pygit2.clone_repository(url, resolve(path), bare=True, remote=_createremote)
