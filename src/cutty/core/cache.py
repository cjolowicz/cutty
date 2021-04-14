"""Application cache."""
import hashlib
import logging
from pathlib import Path
from typing import Iterator
from typing import Optional

from . import exceptions
from . import git
from .compat import contextmanager
from .template import Template
from .versions import Version


logger = logging.getLogger(__name__)


DIGEST_SIZE = hashlib.blake2b.MAX_DIGEST_SIZE


def _hash(value: str) -> str:
    return hashlib.blake2b(value.encode(), digest_size=DIGEST_SIZE).hexdigest()


def _load_repository(location: str, path: Path) -> git.Repository:
    path /= git.Repository.name_from_location(location, bare=True)

    if not path.exists():
        with exceptions.CloneError(location):
            logger.debug(f"Clone {location} to {path}")

            return git.Repository.clone(location, path, mirror=True, quiet=True)

    with exceptions.UpdateError(location):
        logger.debug(f"Fetch {location} to {path}")

        repository = git.Repository(path)
        repository.update_remote(prune=True)
        return repository


class Cache:
    """Application cache."""

    def __init__(self, path: Path) -> None:
        """Initialize."""
        self.path = path

    @contextmanager
    def load(
        self,
        location: str,
        *,
        directory: Optional[Path] = None,
        revision: Optional[str] = None,
    ) -> Iterator[Template]:
        """Load a project template."""
        hash = _hash(location)
        path = self.path / "repositories" / hash[:2] / hash
        repository = _load_repository(location, path)
        version = Version.get(repository, revision=revision)
        worktree = path / "worktrees" / version.sha1

        logger.debug(f"Version {version.name} ({version.sha1})")

        with repository.worktree(
            worktree, version.sha1, detach=True, force_remove=True
        ):
            yield Template.load(
                worktree if directory is None else worktree / directory,
                location=location,
                name=repository.path.stem,
                version=version.name,
            )
