"""Application cache."""
import contextlib
import hashlib
from pathlib import Path
from typing import Iterator

import appdirs

from . import git


appname = "cutty"
path = Path(appdirs.user_cache_dir(appname=appname, appauthor=appname))
repositories = path / "repositories"


def _get_repository_hash(location: str) -> str:
    return hashlib.blake2b(location.encode()).hexdigest()


def _get_repository(location: str) -> git.Repository:
    hash = _get_repository_hash(location)
    path = repositories / hash[:2] / hash / "repo.git"
    return git.Repository(path)


def _get_worktree_path(location: str, sha1: str) -> Path:
    hash = _get_repository_hash(location)
    name = hash[:7]  # This should be stable for Cookiecutter's replay feature.
    return repositories / hash[:2] / hash / "worktrees" / sha1 / name


def repository(location: str) -> git.Repository:
    """Clone or update repository."""
    repository = _get_repository(location)

    if repository.path.exists():
        repository.git("remote", "update")
    else:
        git.git("clone", "--mirror", location, str(repository.path))

    return repository


@contextlib.contextmanager
def worktree(location: str, ref: str) -> Iterator[git.Repository]:
    """Context manager to add and remove a worktree."""
    repository = _get_repository(location)
    sha1 = repository.rev_parse(ref)
    path = _get_worktree_path(location, sha1)
    worktree = repository.add_worktree(path, sha1, detach=True)

    try:
        yield worktree
    finally:
        repository.remove_worktree(path, force=True)


worktree.__annotations__["return"] = contextlib.AbstractContextManager
