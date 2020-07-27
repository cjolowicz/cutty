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

        self.root = _get_repository_root(location)
        path = self.root / "repo.git"

        if path.exists():
            self.repository = git.Repository(path)
            self.repository.update_remote(prune=True)
        else:
            self.repository = git.Repository.clone(
                self.location, destination=path, mirror=True, quiet=True
            )

        if revision is None:
            self.revision = tags.find_latest(self.repository) or "HEAD"
        else:
            self.revision = revision

        self.hash = (
            self.root.name
            if directory is None
            else _get_repository_hash(str(directory))
        )

    @contextlib.contextmanager
    def checkout(self) -> Iterator[git.Repository]:
        """Get a repository with the latest release checked out."""
        sha1 = self.repository.rev_parse(self.revision, verify=True)
        path = _get_worktree_path(self.location, sha1)
        with self.repository.worktree(
            path, sha1, detach=True, force_remove=True
        ) as worktree:
            yield worktree

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


def _get_worktree_path(location: str, sha1: str) -> Path:
    hash = _get_repository_hash(location)
    name = hash[:7]  # This should be stable for Cookiecutter's replay feature.
    return repositories / hash[:2] / hash / "worktrees" / sha1 / name
