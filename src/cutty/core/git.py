"""Git interface."""
from __future__ import annotations

import shutil
import subprocess  # noqa: S404
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from typing import Iterator
from typing import List
from typing import MutableMapping
from typing import Optional
from typing import TypeVar

from .compat import cached_property
from .compat import contextmanager
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
            line = error.stderr.splitlines()[-1]
            if line.startswith("fatal: "):
                message = removeprefix(line, "fatal: ")
            else:
                message = error.stderr

        return cls(command, message)

    def __init__(self, command: str, message: str) -> None:
        """Initialize."""
        self.command = command
        self.message = message

    def __str__(self) -> str:
        """Return a friendly error message, prefixed by the command."""
        return f"git {self.command}: {self.message}"


env: MutableMapping[str, str] = {}


@dataclass
class Git:
    """Git program."""

    path: Path

    @classmethod
    def find(cls) -> Git:
        """Find the Git program."""
        path = shutil.which("git")
        if path is None:
            raise Exception("git not found")
        return cls(Path(path))

    @cached_property
    def version(self) -> str:
        """Return the git version."""
        output = self.run("--version").stdout.strip()
        return removeprefix(output, "git version ")

    def run(self, *args: StrPath, cwd: Optional[Path] = None) -> CompletedProcess:
        """Invoke git."""
        try:
            return subprocess.run(  # noqa: S603
                [self.path, *args],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env or None,
                cwd=cwd,
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


F = TypeVar("F")


def requires(version: str) -> Callable[[F], F]:
    """Document the minimum Git version."""

    def decorator(f: F) -> F:
        return f

    return decorator


class Repository:
    """Git repository."""

    def __init__(
        self, path: Optional[Path] = None, *, git: Optional[Git] = None
    ) -> None:
        """Initialize."""
        self.path = path or Path.cwd()
        self._git = git or Git.find()

    @requires("1.5.6")
    @classmethod
    def init(cls, path: Path) -> Repository:
        """Create a repository."""
        git = Git.find()
        git.run("init", cwd=path)
        return cls(path, git=git)

    @requires("1.6.0")  # --mirror
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
        git = Git.find()
        options = _format_options(quiet=quiet, mirror=mirror)

        if destination is None:
            git.run("clone", *options, location)
        else:
            git.run("clone", *options, location, str(destination))

        return Repository(destination, git=git)

    def git(self, *args: StrPath) -> CompletedProcess:
        """Invoke git."""
        return self._git.run(*args, cwd=self.path)

    @requires("1.5.1")
    def update_remote(self, prune: Optional[bool] = None) -> None:
        """Fetch updates for remotes in the repository."""
        options = _format_options(prune=prune)
        self.git("remote", "update", *options)

    @requires("2.7.0")
    def get_remote_url(self, remote: str) -> str:
        """Retrieve the URL for a remote."""
        process = self.git("remote", "get-url", remote)
        return process.stdout.strip()

    @requires("1.6.1")  # --format ":short"
    def tags(self) -> List[str]:
        """Return the tags."""
        process = self.git(
            "for-each-ref",
            "--format=%(refname:short)",
            "refs/tags",
            stdout=subprocess.PIPE,
        )
        return process.stdout.split()

    @requires("2.9.0")  # --checkout
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

    @requires("2.17.0")
    def remove_worktree(self, path: Path, *, force: Optional[bool] = None) -> None:
        """Remove a worktree."""
        options = _format_options(force=force)
        self.git("worktree", "remove", *options, str(path))

    @contextmanager
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

    @requires("1.2.0")  # --short
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
        process = self.git("rev-parse", *options, rev)
        return process.stdout.strip()

    @requires("1.7.5")  # --max-parents
    def rev_list(
        self,
        *commits: str,
        max_count: Optional[int] = None,
        max_parents: Optional[int] = None,
    ) -> List[str]:
        """Lists commit objects in reverse chronological order."""
        options = _format_options(max_count=max_count, max_parents=max_parents)
        process = self.git("rev-list", *options, *commits)
        return process.stdout.split()

    @requires("1.5.5")  # --exact-match
    def describe(
        self,
        ref: str,
        *,
        tags: Optional[bool] = None,
        exact_match: Optional[bool] = None,
    ) -> str:
        """Give an object a human readable name based on an available ref."""
        options = _format_options(tags=tags, exact_match=exact_match)
        process = self.git("describe", *options, ref)
        return process.stdout.strip()

    @requires("0.99.7")
    def add(self, *paths: StrPath, all: Optional[bool] = None) -> None:
        """Add file contents to the index."""
        options = _format_options(all=all)
        self.git("add", *options, "--", *paths)

    @requires("1.3.0")
    def rm(self, *paths: StrPath) -> None:
        """Remove files from the working tree and from the index."""
        self.git("rm", *paths)

    @requires("1.7.2")  # --allow-empty-message
    def commit(
        self,
        *paths: StrPath,
        allow_empty: Optional[bool] = None,
        allow_empty_message: Optional[bool] = None,
        edit: Optional[bool] = None,
        message: Optional[str] = None,
        verify: Optional[bool] = None,
    ) -> None:
        """Record changes to the repository."""
        options = _format_options(
            allow_empty=allow_empty,
            allow_empty_message=allow_empty_message,
            edit=edit,
            message=message,
            verify=verify,
        )
        self.git("commit", *options, "--", *paths)

    @requires("0.99.1")
    def branch(self, name: str, ref: Optional[str] = None) -> None:
        """Create a branch."""
        if ref is not None:
            self.git("branch", name, ref)
        else:
            self.git("branch", name)

    @requires("0.99")
    def tag(self, name: str, ref: Optional[str] = None) -> None:
        """Create a tag."""
        if ref is not None:
            self.git("tag", name, ref)
        else:
            self.git("tag", name)

    @requires("0.99.7")
    def merge(self, ref: str) -> None:
        """Join two development histories together."""
        self.git("merge", ref)

    @requires("0.99.6")
    def cherrypick(self, *commits: str, commit: Optional[bool] = None) -> None:
        """Apply the changes introduced by some existing commits."""
        options = _format_options(commit=commit)
        self.git("cherry-pick", *options, *commits)
