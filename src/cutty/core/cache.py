"""Application cache."""
import hashlib
from pathlib import Path
from typing import Iterator
from typing import Optional

from . import exceptions
from . import git
from . import locations
from .compat import contextmanager
from .template import Template
from .versions import Version


def _hash(value: str) -> str:
    return hashlib.blake2b(value.encode()).hexdigest()


def _load_repository(location: str, path: Path) -> git.Repository:
    if not path.exists():
        with exceptions.CloneError(location):
            return git.Repository.clone(
                location, destination=path, mirror=True, quiet=True
            )

    with exceptions.UpdateError(location):
        repository = git.Repository(path)
        repository.update_remote(prune=True)
        return repository


class Cache:
    """Application cache."""

    def __init__(self, path: Path) -> None:
        """Initialize."""
        self.path = path

    def _get_template_path(self, location: str) -> Path:
        hash = _hash(location)
        return self.path / "repositories" / hash[:2] / hash

    @contextmanager
    def load(
        self,
        location: str,
        *,
        directory: Optional[Path] = None,
        revision: Optional[str] = None,
    ) -> Iterator[Template]:
        """Load a project template."""
        path = self._get_template_path(location)
        repository = _load_repository(location, path / "repo.git")
        version = Version.get(repository, revision=revision)
        worktree = path / "worktrees" / version.sha1

        with repository.worktree(
            worktree, version.sha1, detach=True, force_remove=True
        ):
            yield Template.load(
                worktree if directory is None else worktree / directory,
                location=location,
                version=version.name,
            )


cache = Cache(locations.cache)
