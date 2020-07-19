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


def removeprefix(string: str, prefix: str) -> str:
    """Remove prefix from string, if present."""
    return string[len(prefix) :] if string.startswith(prefix) else string


class Error(Exception):
    """Git error."""

    def __init__(self, error: subprocess.CalledProcessError) -> None:
        """Initialize."""
        self.error = error

    @property
    def command(self) -> str:
        """Return the git command."""
        return "".join(self.error.cmd[1:2])

    @property
    def message(self) -> str:
        """Return a friendly error message."""
        if (
            self.command == "rev-parse"
            and "Needed a single revision" in self.error.stderr
        ):
            return f"unknown revision {self.error.cmd[-1]!r}"

        if not self.error.stderr:
            return f"returned non-zero exit status {self.error.returncode}"

        message = self.error.stderr.splitlines()[-1]
        return removeprefix(message, "fatal: ")

    def __str__(self) -> str:
        """Return a friendly error message, prefixed by the command."""
        return f"git {self.command}: {self.message}"


def git(*args: str, check: bool = True, **kwargs: Any) -> CompletedProcess:
    """Invoke git."""
    try:
        return subprocess.run(  # noqa: S603,S607
            ["git", *args], check=check, stderr=subprocess.PIPE, text=True, **kwargs
        )
    except subprocess.CalledProcessError as error:
        raise Error(error) from None


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

    @classmethod
    def clone(
        cls,
        location: str,
        *,
        destination: Optional[Path] = None,
        quiet: bool = False,
        mirror: bool = False,
    ) -> Repository:
        """Clone a repository."""
        options = _format_boolean_options(quiet=quiet, mirror=mirror)

        if destination is None:
            git("clone", *options, location)
        else:
            git("clone", *options, location, str(destination))

        return Repository(destination)

    def git(self, *args: str, **kwargs: Any) -> CompletedProcess:
        """Invoke git."""
        return git(*args, cwd=self.path, **kwargs)

    def update_remote(self, prune: bool = False) -> None:
        """Fetch updates for remotes in the repository."""
        options = _format_boolean_options(prune=prune)
        self.git("remote", "update", *options, stdout=subprocess.PIPE)

    def tags(self) -> List[str]:
        """Return the tags."""
        process = self.git(
            "for-each-ref",
            "--format=%(refname:short)",
            "refs/tags",
            stdout=subprocess.PIPE,
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
        process = self.git("rev-parse", "--verify", rev, stdout=subprocess.PIPE)
        return process.stdout.strip()
