"""Project."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from . import git
from . import locations
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

    @classmethod
    def create(cls, path: Path, *, name: str, version: str) -> Project:
        """Create the project."""
        repository = git.Repository.init(path)
        branch = f"{locations.name}/{name}"

        repository.add(all=True)
        repository.commit(message=f"Generate project from {name} {version}")
        repository.branch(branch)

        return cls.load(path)

    @contextmanager
    def update(self, *, name: str, version: str) -> Iterator[Path]:
        """Update the project."""
        branch = f"{locations.name}/{name}"
        self._ensure_branch_exists(branch)

        with self.repository.worktree(
            self.repository.path / ".git" / locations.name / name,
            branch,
            checkout=False,
            force_remove=True,
        ) as worktree:
            yield worktree.path

            worktree.add(all=True)
            worktree.commit(message=f"Update {name} to {version}", verify=False)

        self.repository.cherrypick(branch, commit=False)
        self.repository.commit(edit=False)  # Run pre-commit hook

    def _ensure_branch_exists(self, branch: str) -> None:
        try:
            self.repository.rev_parse(branch, verify=True, quiet=True)
        except git.Error:
            (firstref,) = self.repository.rev_list("HEAD", max_count=1, max_parents=0)
            self.repository.branch(branch, firstref)
