"""Application cache."""
import contextlib
import hashlib
from pathlib import Path
from typing import Iterator
from typing import Optional

import appdirs

from . import git
from . import tags


appname = "cutty"
path = Path(appdirs.user_cache_dir(appname=appname, appauthor=appname))
repositories = path / "repositories"


def _get_repository_hash(location: str) -> str:
    # Avoid "Filename too long" error with Git for Windows.
    # https://stackoverflow.com/a/22575737/1355754
    return hashlib.blake2b(location.encode()).hexdigest()[:64]


def _get_repository_path(location: str) -> Path:
    hash = _get_repository_hash(location)
    return repositories / hash[:2] / hash / "repo.git"


def _get_repository(location: str) -> git.Repository:
    path = _get_repository_path(location)
    return git.Repository(path)


def _get_worktree_path(location: str, sha1: str) -> Path:
    hash = _get_repository_hash(location)
    name = hash[:7]  # This should be stable for Cookiecutter's replay feature.
    return repositories / hash[:2] / hash / "worktrees" / sha1 / name


def repository_hash(location: str, *, directory: Optional[Path] = None) -> str:
    """Return a unique hash for the template."""
    return _get_repository_hash(
        location if directory is None else "/".join((location, *directory.parts))
    )


def repository(location: str) -> git.Repository:
    """Clone or update repository."""
    path = _get_repository_path(location)

    if path.exists():
        repository = git.Repository(path)
        repository.update_remote(prune=True)
    else:
        repository = git.Repository.clone(
            location, destination=path, mirror=True, quiet=True
        )

    return repository


@contextlib.contextmanager
def worktree(location: str, ref: str) -> Iterator[git.Repository]:
    """Context manager to add and remove a worktree."""
    repository = _get_repository(location)
    sha1 = repository.rev_parse(ref, verify=True)
    path = _get_worktree_path(location, sha1)
    with repository.worktree(path, sha1, detach=True, force_remove=True) as worktree:
        yield worktree


worktree.__annotations__["return"] = contextlib.AbstractContextManager


@contextlib.contextmanager
def checkout(
    location: str, *, revision: Optional[str] = None
) -> Iterator[git.Repository]:
    """Get a repository with the latest release checked out."""
    repository_ = repository(location)
    if revision is None:
        revision = tags.find_latest(repository_) or "HEAD"
    with worktree(location, revision) as worktree_:
        yield worktree_


checkout.__annotations__["return"] = contextlib.AbstractContextManager
