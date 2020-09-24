"""Template."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from . import exceptions
from .hooks import Hooks
from .variables import Variables


def find_template(path: Path) -> Optional[Path]:
    """Determine which child directory is the project template."""
    for item in path.iterdir():
        if (
            item.is_dir()
            and "cookiecutter" in item.name
            and "{{" in item.name
            and "}}" in item.name
        ):
            return item

    return None


@dataclass(frozen=True)
class Template:
    """Template."""

    root: Path
    hooks: Hooks
    repository: Path
    version: str
    variables: Variables

    @classmethod
    def load(cls, path: Path, *, version: str, location: str) -> Template:
        """Load the template variables."""
        root = find_template(path)
        if root is None:
            raise exceptions.TemplateDirectoryNotFound(location)

        hooks = Hooks.load(path / "hooks")
        variables = Variables.load(path / "cookiecutter.json", location=location)

        return cls(
            root=root,
            hooks=hooks,
            repository=path,
            version=version,
            variables=variables,
        )

    @property
    def name(self) -> str:
        """Return the template name."""
        return self.repository.stem
