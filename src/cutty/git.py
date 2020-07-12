"""Git interface."""
from __future__ import annotations

import subprocess  # noqa: S404
from pathlib import Path
from typing import Any
from typing import List
from typing import Optional
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    CompletedProcess = subprocess.CompletedProcess[str]  # pragma: no cover
else:
    CompletedProcess = subprocess.CompletedProcess


def git(*args: str, check: bool = True, **kwargs: Any) -> CompletedProcess:
    """Invoke git."""
    return subprocess.run(["git", *args], check=check, **kwargs)  # noqa: S603,S607


def _format_boolean_options(**kwargs: bool) -> List[str]:
    """Convert keyword arguments to boolean command-line options."""
    return [f"--{key}" for key, value in kwargs.items() if value]


class Repository:
    """Git repository."""

    def __init__(self, path: Optional[Path] = None) -> None:
        """Initialize."""
        self.path = path or Path.cwd()

    @classmethod
    def init(cls, path: Path) -> Repository:
        """Create a repository."""
        git("init", cwd=path)
        return cls(path)

    def git(self, *args: str, **kwargs: Any) -> CompletedProcess:
        """Invoke git."""
        return git(*args, cwd=self.path, **kwargs)

    def tags(self) -> List[str]:
        """Return the tags."""
        process = self.git(
            "for-each-ref",
            "--format=%(refname:short)",
            "refs/tags",
            capture_output=True,
            text=True,
        )
        return process.stdout.split()

    def add_worktree(self, path: Path, ref: str, *, detach: bool = False) -> Repository:
        """Add a worktree."""
        options = _format_boolean_options(detach=detach)
        self.git("worktree", "add", *options, str(path), ref)

        return Repository(path)

    def remove_worktree(self, path: Path, *, force: bool = False) -> None:
        """Remove a worktree."""
        options = _format_boolean_options(force=force)
        self.git("worktree", "remove", *options, str(path))

    def rev_parse(self, rev: str) -> str:
        """Return the SHA1 hash for the given revision."""
        process = self.git(
            "rev-parse", "--verify", "--quiet", rev, capture_output=True, text=True,
        )
        return process.stdout.strip()
