"""Template."""
from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace
from pathlib import Path
from typing import List
from typing import Optional

from . import exceptions
from .variables import Variable
from .variables import Variables


def find_template(path: Path) -> Optional[Path]:
    """Determine which child directory is the project template."""
    for item in path.iterdir():
        if "cookiecutter" in item.name and "{{" in item.name and "}}" in item.name:
            return item

    return None


def as_string_list(variable: Variable) -> List[str]:
    """Check that the value is a list of strings, and return it."""
    if not (
        isinstance(variable.value, list)
        and all(isinstance(item, str) for item in variable.value)
    ):
        raise exceptions.InvalidTemplateVariable(
            variable.name, "cookiecutter.json", "List[str]", variable.value
        )

    return variable.value


@dataclass(frozen=True)
class Template:
    """Template."""

    root: Path
    hookdir: Path
    repository: Path
    version: str
    variables: Variables

    @staticmethod
    def load_location(instance: Path) -> str:
        """Return the location specified in the given instance."""
        path = instance / ".cookiecutter.json"
        variables = Variables.load(path)

        with exceptions.MissingTemplateVariable("_template", path).when(KeyError):
            location = variables["_template"].value

        if not isinstance(location, str):
            raise exceptions.InvalidTemplateVariable(
                "_template", path, "str", type(location).__name__
            )

        return location

    @classmethod
    def load(cls, path: Path, *, version: str, location: str) -> Template:
        """Load the template variables."""
        root = find_template(path)
        if root is None:
            raise exceptions.TemplateDirectoryNotFound(location)

        hookdir = path / "hooks"
        variables = Variables.load(path / "cookiecutter.json", location=location)

        return cls(
            root=root,
            hookdir=hookdir,
            repository=path,
            version=version,
            variables=variables,
        )

    @property
    def extensions(self) -> List[str]:
        """Return the Jinja extensions."""
        variable = self.variables.get("_extensions", default=[])
        return as_string_list(variable)

    @property
    def copy_without_render(self) -> List[str]:
        """Return patterns for files to be copied without rendering."""
        variable = self.variables.get("_copy_without_render", default=[])
        return as_string_list(variable)

    def override(self, instance: Path) -> Template:
        """Override template configuration from an existing instance."""
        instance_variables = Variables.load(instance / ".cookiecutter.json")
        variables = self.variables.override(instance_variables)
        return replace(self, variables=variables)
