"""Application cache."""
import hashlib
import json
from pathlib import Path
from typing import cast
from typing import Iterator
from typing import Optional

from . import git
from . import locations
from . import tags
from .compat import contextmanager
from .types import Context


repositories = locations.cache / "repositories"


def _clone_or_update(location: str, path: Path) -> git.Repository:
    if not path.exists():
        return git.Repository.clone(location, destination=path, mirror=True, quiet=True)

    repository = git.Repository(path)
    repository.update_remote(prune=True)
    return repository


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
        # Avoid "Filename too long" error with Git for Windows.
        # https://stackoverflow.com/a/22575737/1355754
        hash = hashlib.blake2b(location.encode()).hexdigest()[:64]
        self.root = repositories / hash[:2] / hash
        self.repository = _clone_or_update(location, self.root / "repo.git")
        self.directory = directory
        self.revision = revision or tags.find_latest(self.repository) or "HEAD"
        self.describe = tags.describe(self.repository, ref=self.revision)
        self.context = self.root / (
            "context.json" if not directory else f"context-{directory}.json"
        )

    @contextmanager
    def checkout(self) -> Iterator[Path]:
        """Get a repository with the latest release checked out."""
        sha1 = self.repository.rev_parse(self.revision, verify=True)
        path = self.root / "worktrees" / sha1
        with self.repository.worktree(
            path, sha1, detach=True, force_remove=True
        ) as worktree:
            yield (
                worktree.path
                if self.directory is None
                else worktree.path / self.directory
            )

    def load_context(self) -> Context:
        """Load the context."""
        with self.context.open() as io:
            context = json.load(io)

        return cast(Context, context)

    def dump_context(self, context: Context) -> None:
        """Dump the context."""
        with self.context.open(mode="w") as io:
            json.dump(context, io, indent=2)
