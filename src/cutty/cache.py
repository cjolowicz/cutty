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
        entry = _Entry(location, directory=directory, revision=revision)
        with entry.checkout() as repository:
            yield cls(repository, entry.version, entry.context)


def _clone_or_update(location: str, path: Path) -> git.Repository:
    if not path.exists():
        return git.Repository.clone(location, destination=path, mirror=True, quiet=True)

    repository = git.Repository(path)
    repository.update_remote(prune=True)
    return repository


class _Entry:
    """Internal cache entry for a project template."""

    def __init__(
        self,
        location: str,
        *,
        directory: Optional[Path] = None,
        revision: Optional[str] = None,
    ) -> None:
        """Initialize."""
        # Avoid "Filename too long" error with Git for Windows.
        # https://stackoverflow.com/a/22575737/1355754
        hash = hashlib.blake2b(location.encode()).hexdigest()[:64]
        path = locations.cache / "repositories" / hash[:2] / hash
        repository = _clone_or_update(location, path / "repo.git")
        if revision is None:
            revision = tags.find_latest(repository) or "HEAD"
        sha1 = repository.rev_parse(revision, verify=True)

        self.repository = repository
        self.directory = directory
        self.version = tags.describe(repository, ref=revision)
        self.worktree = path / "worktrees" / sha1
        self.context = path / (
            "context.json" if not directory else f"context-{directory}.json"
        )

    @contextmanager
    def checkout(self) -> Iterator[Path]:
        """Get a repository with the latest release checked out."""
        with self.repository.worktree(
            self.worktree, self.worktree.name, detach=True, force_remove=True
        ):
            yield (
                self.worktree
                if self.directory is None
                else self.worktree / self.directory
            )
