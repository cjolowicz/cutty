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

    repository: Path
    name: str
    version: str
    variables: Variables
    hooks: Hooks

    @classmethod
    def load(cls, path: Path, *, name: str, version: str, location: str) -> Template:
        """Load the template variables."""
        variables = Variables.load(path / "cookiecutter.json", location=location)
        hooks = Hooks.load(path / "hooks")

        return cls(
            repository=path,
            name=name,
            version=version,
            variables=variables,
            hooks=hooks,
        )

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
