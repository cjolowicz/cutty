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

        hash = _hash_location(self.location)
        self.root = repositories / hash[:2] / hash
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

        self.hash_with_directory = (
            self.root.name if directory is None else _hash_location(str(directory))
        )

    @contextlib.contextmanager
    def checkout(self) -> Iterator[git.Repository]:
        """Get a repository with the latest release checked out."""
        sha1 = self.repository.rev_parse(self.revision, verify=True)
        hash = self.root.name
        name = hash[:7]  # This should be stable for Cookiecutter's replay feature.
        path = repositories / hash[:2] / hash / "worktrees" / sha1 / name
        with self.repository.worktree(
            path, sha1, detach=True, force_remove=True
        ) as worktree:
            yield worktree

    checkout.__annotations__["return"] = contextlib.AbstractContextManager

    def load_context(self) -> StrMapping:
        """Load the context for replay."""
        context = replay.load(str(self.root), self.hash_with_directory)
        return cast(StrMapping, context)

    def dump_context(self, context: StrMapping) -> None:
        """Dump the context for replay."""
        replay.dump(str(self.root), self.hash_with_directory, context)


def _hash_location(location: str, *, length: int = 64) -> str:
    # Avoid "Filename too long" error with Git for Windows.
    # https://stackoverflow.com/a/22575737/1355754
    return hashlib.blake2b(location.encode()).hexdigest()[:length]
