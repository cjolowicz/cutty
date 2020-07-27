"""Application cache."""
import contextlib
import hashlib
from pathlib import Path
from typing import cast
from typing import Iterator
from typing import Optional

import appdirs
from cookiecutter import replay

from . import git
from . import tags
from .types import StrMapping


appname = "cutty"
path = Path(appdirs.user_cache_dir(appname=appname, appauthor=appname))
repositories = path / "repositories"


class Entry:
    """Cache entry for a repository."""

    def __init__(
        self,
        location: str,
        *,
        directory: Optional[Path] = None,
        revision: Optional[str] = None,
    ) -> None:
        """Initialize."""
        self.location = location
        self.directory = directory
        self.repository = repository(self.location)
        if revision is None:
            self.revision = tags.find_latest(self.repository) or "HEAD"
        else:
            self.revision = revision
        self.root = _get_repository_root(location)
        self.hash = (
            self.root.name
            if directory is None
            else _get_repository_hash(str(directory))
        )

    @contextlib.contextmanager
    def checkout(self) -> Iterator[git.Repository]:
        """Get a repository with the latest release checked out."""
        with worktree(self.location, self.revision) as worktree_:
            yield worktree_

    checkout.__annotations__["return"] = contextlib.AbstractContextManager

    def load_context(self) -> StrMapping:
        """Load the context for replay."""
        context = replay.load(str(self.root), self.hash)
        return cast(StrMapping, context)

    def dump_context(self, context: StrMapping) -> None:
        """Dump the context for replay."""
        replay.dump(str(self.root), self.hash, context)


def _get_repository_hash(location: str, *, length: int = 64) -> str:
    # Avoid "Filename too long" error with Git for Windows.
    # https://stackoverflow.com/a/22575737/1355754
    return hashlib.blake2b(location.encode()).hexdigest()[:length]


def _get_repository_root(location: str) -> Path:
    hash = _get_repository_hash(location)
    return repositories / hash[:2] / hash


def _get_repository_path(location: str) -> Path:
    return _get_repository_root(location) / "repo.git"


def _get_repository(location: str) -> git.Repository:
    path = _get_repository_path(location)
    return git.Repository(path)


def _get_worktree_path(location: str, sha1: str) -> Path:
    hash = _get_repository_hash(location)
    name = hash[:7]  # This should be stable for Cookiecutter's replay feature.
    return repositories / hash[:2] / hash / "worktrees" / sha1 / name


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
