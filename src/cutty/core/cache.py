"""Application cache."""
import hashlib
from pathlib import Path
from typing import Iterator
from typing import Optional
from typing import Tuple

from . import git
from . import locations
from . import tags
from . import template
from .compat import contextmanager
from .template import Template


def _hash(value: str) -> str:
    return hashlib.blake2b(value.encode()).hexdigest()


def _load_repository(location: str, path: Path) -> git.Repository:
    if not path.exists():
        return git.Repository.clone(location, destination=path, mirror=True, quiet=True)

    repository = git.Repository(path)
    repository.update_remote(prune=True)
    return repository


def _determine_version(
    repository: git.Repository, revision: Optional[str]
) -> Tuple[str, str]:
    if revision is None:
        revision = tags.find_latest(repository) or "HEAD"
    sha1 = repository.rev_parse(revision, verify=True)
    version = tags.describe(repository, ref=revision)
    return version, sha1


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
        overrides: Optional[template.Config] = None
    ) -> Iterator[Template]:
        """Load a project template."""
        path = self._get_template_path(location)
        repository = _load_repository(location, path / "repo.git")
        version, sha1 = _determine_version(repository, revision)
        worktree = path / "worktrees" / sha1

        with repository.worktree(worktree, sha1, detach=True, force_remove=True):
            yield Template.load(
                worktree if directory is None else worktree / directory,
                location=location,
                version=version,
                overrides=overrides,
            )


cache = Cache(locations.cache)
