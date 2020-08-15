"""Application cache."""
import contextlib
import hashlib
import json
from pathlib import Path
from typing import cast
from typing import Iterator
from typing import Optional

from . import git
from . import locations
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
        # Avoid "Filename too long" error with Git for Windows.
        # https://stackoverflow.com/a/22575737/1355754
        hash = hashlib.blake2b(location.encode()).hexdigest()[:64]
        self.root = repositories / hash[:2] / hash
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
        self.context = self.root / (
            "context.json" if not self.directory else f"context-{self.directory}.json"
        )

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
        """Load the context."""
        with self.context.open() as io:
            context = json.load(io)

        return cast(StrMapping, context)

    def dump_context(self, context: StrMapping) -> None:
        """Dump the context."""
        with self.context.open(mode="w") as io:
            json.dump(context, io, indent=2)
