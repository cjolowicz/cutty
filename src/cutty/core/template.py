"""Template."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from . import exceptions
from .compat import cached_property
from .hooks import Hooks
from .variables import Variables


@dataclass(frozen=True)
class Template:
    """Template."""

    hooks: Hooks
    repository: Path
    version: str
    variables: Variables

    @classmethod
    def load(cls, path: Path, *, version: str, location: str) -> Template:
        """Load the template variables."""
        hooks = Hooks.load(path / "hooks")
        variables = Variables.load(path / "cookiecutter.json", location=location)

        return cls(hooks=hooks, repository=path, version=version, variables=variables)

    @cached_property
    def root(self) -> Path:
        """Return the template directory."""
        for path in self.repository.iterdir():
            if (
                path.is_dir()
                and "cookiecutter" in path.name
                and "{{" in path.name
                and "}}" in path.name
            ):
                return path

        raise exceptions.TemplateDirectoryNotFound(self.variables.location)

    @property
    def name(self) -> str:
        """Return the template name."""
        return self.repository.stem
