"""Project."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from . import git
from .compat import contextmanager
from .variables import Variables


@dataclass
class Project:
    """Project."""

    repository: git.Repository
    variables: Variables

    @classmethod
    def load(cls, path: Path) -> Project:
        """Load the project."""
        repository = git.Repository(path)
        variables = Variables.load(path / ".cookiecutter.json")

        return cls(repository, variables)

    @contextmanager
    def worktree(self, *, commit_message: str) -> Iterator[Path]:
        """Create an empty worktree for a commit."""
        self._ensure_branch_exists("template")

        with self.repository.worktree(
            self.repository.path / ".git" / "cutty" / self.repository.path.name,
            "template",
            checkout=False,
            force_remove=True,
        ) as worktree:
            yield worktree.path

            worktree.add(all=True)
            worktree.commit(message=commit_message, verify=False)

            commit = worktree.rev_parse("HEAD")

        self.repository.cherrypick(commit)

    def _ensure_branch_exists(self, branch: str) -> None:
        try:
            self.repository.rev_parse(branch, verify=True, quiet=True)
        except git.Error:
            (firstref,) = self.repository.rev_list(max_count=1, max_parents=0)
            self.repository.branch(branch, firstref)
