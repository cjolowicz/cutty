"""Application cache."""
import contextlib
import hashlib
from pathlib import Path
from typing import cast
from typing import Iterator
from typing import Optional

from . import git
from . import locations
from . import replay
from . import tags
from .types import StrMapping


repositories = locations.cache / "repositories"


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
        self.hash = _hash_location(location)
        self.root = repositories / self.hash[:2] / self.hash
        self.directory = directory

        repository_path = self.root / "repo.git"

        if repository_path.exists():
            self.repository = git.Repository(repository_path)
            self.repository.update_remote(prune=True)
        else:
            self.repository = git.Repository.clone(
                location, destination=repository_path, mirror=True, quiet=True
            )

        if revision is None:
            self.revision = tags.find_latest(self.repository) or "HEAD"
        else:
            self.revision = revision

        self.describe = tags.describe(self.repository, ref=self.revision)

        if directory is None:
            self.replay_hash = self.hash
        else:
            self.replay_hash = _hash_location(str(directory))

    @contextlib.contextmanager
    def checkout(self) -> Iterator[Path]:
        """Get a repository with the latest release checked out."""
        sha1 = self.repository.rev_parse(self.revision, verify=True)
        path = self.root / "worktrees" / sha1
        with self.repository.worktree(
            path, sha1, detach=True, force_remove=True
        ) as worktree:
            if self.directory is not None:
                yield worktree.path / self.directory
            else:
                yield worktree.path

    checkout.__annotations__["return"] = contextlib.AbstractContextManager

    def load_context(self) -> StrMapping:
        """Load the context for replay."""
        context = replay.load(str(self.root), self.replay_hash)
        return cast(StrMapping, context)

    def dump_context(self, context: StrMapping) -> None:
        """Dump the context for replay."""
        replay.dump(str(self.root), self.replay_hash, context)


def _hash_location(location: str, *, length: int = 64) -> str:
    # Avoid "Filename too long" error with Git for Windows.
    # https://stackoverflow.com/a/22575737/1355754
    return hashlib.blake2b(location.encode()).hexdigest()[:length]
