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
from .utils import removeprefix


class Error(Exception):
    """Git error."""

    @classmethod
    def from_subprocess(cls, error: subprocess.CalledProcessError) -> Error:
        """Create an error from subprocess.CalledProcessError."""
        command = "".join(error.cmd[1:2])

        if command == "rev-parse" and "Needed a single revision" in error.stderr:
            message = f"unknown revision {error.cmd[-1]!r}"
        elif not error.stderr:
            message = f"returned non-zero exit status {error.returncode}"
        else:
            message = error.stderr.splitlines()[-1]
            message = removeprefix(message, "fatal: ")

        return cls(command, message)

    def __init__(self, command: str, message: str) -> None:
        """Initialize."""
        self.command = command
        self.message = message

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
        raise Error.from_subprocess(error) from None


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
        self,
        rev: str,
        *,
        quiet: Optional[bool] = None,
        short: Optional[bool] = None,
        verify: Optional[bool] = None,
    ) -> str:
        """Return the SHA1 hash for the given revision."""
        options = _format_options(quiet=quiet, short=short, verify=verify)
        process = self.git("rev-parse", *options, rev, stdout=subprocess.PIPE)
        return process.stdout.strip()

    def rev_list(
        self,
        *commits: str,
        max_count: Optional[int] = None,
        max_parents: Optional[int] = None,
    ) -> List[str]:
        """Lists commit objects in reverse chronological order."""
        options = _format_options(max_count=max_count, max_parents=max_parents)
        process = self.git("rev-list", *options, *commits, stdout=subprocess.PIPE)
        return process.stdout.split()

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
