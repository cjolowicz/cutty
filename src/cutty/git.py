"""Git interface."""
from __future__ import annotations

import contextlib
import subprocess  # noqa: S404
from pathlib import Path
from typing import Any
from typing import Iterator
from typing import List
from typing import MutableMapping
from typing import Optional
from typing import TypeVar

from .types import CompletedProcess
from .types import StrPath


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


env: MutableMapping[str, str] = {}


def git(*args: StrPath, check: bool = True, **kwargs: Any) -> CompletedProcess:
    """Invoke git."""
    try:
        return subprocess.run(  # noqa: S603,S607
            ["git", *args],
            check=check,
            stderr=subprocess.PIPE,
            text=True,
            env=env or None,
            **kwargs,
        )
    except subprocess.CalledProcessError as error:
        raise Error(error) from None


T = TypeVar("T")


def _format_option(key: str, value: T) -> str:
    """Convert a key-value pair to a command-line option."""
    name = key.replace("_", "-")
    if isinstance(value, bool):
        return f"--{name}" if value else f"--no-{name}"
    else:
        return f"--{name}={value}"


def _format_options(**kwargs: Optional[T]) -> List[str]:
    """Convert keyword arguments to command-line options."""
    return [
        _format_option(key, value) for key, value in kwargs.items() if value is not None
    ]


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
        quiet: Optional[bool] = None,
        mirror: Optional[bool] = None,
    ) -> Repository:
        """Clone a repository."""
        options = _format_options(quiet=quiet, mirror=mirror)

        if destination is None:
            git("clone", *options, location)
        else:
            git("clone", *options, location, str(destination))

        return Repository(destination)

    def git(self, *args: StrPath, **kwargs: Any) -> CompletedProcess:
        """Invoke git."""
        return git(*args, cwd=self.path, **kwargs)

    def update_remote(self, prune: Optional[bool] = None) -> None:
        """Fetch updates for remotes in the repository."""
        options = _format_options(prune=prune)
        self.git("remote", "update", *options, stdout=subprocess.PIPE)

    def get_remote_url(self, remote: str) -> str:
        """Retrieve the URL for a remote."""
        process = self.git("remote", "get-url", remote, stdout=subprocess.PIPE)
        return process.stdout.strip()

    def tags(self) -> List[str]:
        """Return the tags."""
        process = self.git(
            "for-each-ref",
            "--format=%(refname:short)",
            "refs/tags",
            stdout=subprocess.PIPE,
        )
        return process.stdout.split()

    def add_worktree(
        self,
        path: Path,
        ref: str,
        *,
        checkout: Optional[bool] = None,
        detach: Optional[bool] = None,
    ) -> Repository:
        """Add a worktree."""
        options = _format_options(checkout=checkout, detach=detach)
        self.git("worktree", "add", *options, str(path), ref)

        return Repository(path)

    def remove_worktree(self, path: Path, *, force: Optional[bool] = None) -> None:
        """Remove a worktree."""
        options = _format_options(force=force)
        self.git("worktree", "remove", *options, str(path))

    @contextlib.contextmanager
    def worktree(
        self,
        path: Path,
        ref: str,
        *,
        checkout: Optional[bool] = None,
        detach: Optional[bool] = None,
        force_remove: Optional[bool] = None,
    ) -> Iterator[Repository]:
        """Context manager to add and remove a worktree."""
        worktree = self.add_worktree(path, ref, checkout=checkout, detach=detach)

        try:
            yield worktree
        finally:
            self.remove_worktree(path, force=force_remove)

    worktree.__annotations__["return"] = contextlib.AbstractContextManager

    def rev_parse(
        self, rev: str, *, short: Optional[bool] = None, verify: Optional[bool] = None
    ) -> str:
        """Return the SHA1 hash for the given revision."""
        options = _format_options(short=short, verify=verify)
        process = self.git("rev-parse", *options, rev, stdout=subprocess.PIPE)
        return process.stdout.strip()

    def describe(
        self, ref: str, *, tags: Optional[bool] = None, exact: Optional[bool] = None,
    ) -> str:
        """Give an object a human readable name based on an available ref."""
        options = _format_options(tags=tags, exact=exact)
        process = self.git("describe", *options, ref, stdout=subprocess.PIPE)
        return process.stdout.strip()

    def add(self, *paths: StrPath, all: Optional[bool] = None) -> None:
        """Add file contents to the index."""
        options = _format_options(all=all)
        self.git("add", *options, "--", *paths)

    def rm(self, *paths: StrPath) -> None:
        """Remove files from the working tree and from the index."""
        self.git("rm", *paths)

    def commit(
        self,
        *paths: StrPath,
        allow_empty: Optional[bool] = None,
        allow_empty_message: Optional[bool] = None,
        message: Optional[str] = None,
    ) -> None:
        """Record changes to the repository."""
        options = _format_options(
            allow_empty=allow_empty,
            allow_empty_message=allow_empty_message,
            message=message,
        )
        self.git("commit", *options, "--", *paths)

    def branch(self, name: str) -> None:
        """Create a branch."""
        self.git("branch", name)

    def tag(self, name: str, ref: Optional[str] = None) -> None:
        """Create a tag."""
        if ref is not None:
            self.git("tag", name, ref)
        else:
            self.git("tag", name)

    def merge(self, ref: str) -> None:
        """Join two development histories together."""
        self.git("merge", ref)
