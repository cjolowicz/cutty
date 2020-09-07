"""Application cache."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator
from typing import Optional

from . import git
from . import tags
from .. import locations
from ..compat import contextmanager


def _hash(value: str) -> str:
    # Avoid "Filename too long" error with Git for Windows.
    # https://stackoverflow.com/a/22575737/1355754
    return hashlib.blake2b(value.encode()).hexdigest()[:64]


def _load_repository(location: str, path: Path) -> git.Repository:
    if not path.exists():
        return git.Repository.clone(location, destination=path, mirror=True, quiet=True)

    repository = git.Repository(path)
    repository.update_remote(prune=True)
    return repository


@dataclass
class Cache:
    """Cache for a project template."""

    repository: Path
    version: str

    @classmethod
    @contextmanager
    def load(
        cls,
        location: str,
        *,
        directory: Optional[Path] = None,
        revision: Optional[str] = None,
    ) -> Iterator[Cache]:
        """Load the project template from the cache."""
        hash = _hash(location)
        path = locations.cache / "repositories" / hash[:2] / hash
        repository = _load_repository(location, path / "repo.git")
        if revision is None:
            revision = tags.find_latest(repository) or "HEAD"
        sha1 = repository.rev_parse(revision, verify=True)
        version = tags.describe(repository, ref=revision)
        worktree = path / "worktrees" / sha1

        with repository.worktree(worktree, sha1, detach=True, force_remove=True):
            if directory is not None:
                hash = _hash(str(directory))
                worktree = worktree / directory

            yield cls(worktree, version)
