"""Application cache."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator
from typing import Optional

from . import git
from . import locations
from . import tags
from .compat import contextmanager


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
    context: Path

    @contextmanager
    @classmethod
    def load(
        cls,
        location: str,
        *,
        directory: Optional[Path] = None,
        revision: Optional[str] = None,
    ) -> Iterator[Cache]:
        """Load the project template from the cache."""
        # Avoid "Filename too long" error with Git for Windows.
        # https://stackoverflow.com/a/22575737/1355754
        hash = hashlib.blake2b(location.encode()).hexdigest()[:64]
        path = locations.cache / "repositories" / hash[:2] / hash
        repository = _load_repository(location, path / "repo.git")
        if revision is None:
            revision = tags.find_latest(repository) or "HEAD"
        sha1 = repository.rev_parse(revision, verify=True)
        version = tags.describe(repository, ref=revision)
        context = path / "context.json"
        worktree = path / "worktrees" / sha1

        with repository.worktree(worktree, sha1, detach=True, force_remove=True):
            if directory is not None:
                context = path / f"context-{directory}.json"
                worktree = worktree / directory

            yield cls(worktree, version, context)
