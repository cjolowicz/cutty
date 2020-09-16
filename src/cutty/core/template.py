"""Template."""
from __future__ import annotations

import json
from dataclasses import dataclass
from dataclasses import replace
from pathlib import Path
from typing import Any
from typing import cast
from typing import Iterable
from typing import Iterator
from typing import List
from typing import Optional

from . import exceptions


@dataclass(frozen=True)
class Variable:
    """Template variable."""

    name: str
    value: Any


class Variables:
    """Collection of template variables."""

    @classmethod
    def load(cls, path: Path, *, location: str) -> Variables:
        """Load the template variables from a JSON file."""
        with path.open() as io:
            data = json.load(io)
            data["_template"] = location

        return cls(Variable(name, value) for name, value in data.items())

    def __init__(self, variables: Iterable[Variable]) -> None:
        """Initialize."""
        self.variables = {variable.name: variable for variable in variables}

    def __iter__(self) -> Iterator[Variable]:
        """Iterate over the variables in the collection."""
        return iter(self.variables.values())

    def __getitem__(self, name: str) -> Variable:
        """Retrieve a variable by name."""
        return self.variables[name]

    def override(self, other: Variables) -> Variables:
        """Override variables from another collection."""

        def _override(variable: Variable) -> Variable:
            if variable.name.startswith("_"):
                return variable

            for other_variable in other.variables:
                if variable.name == other_variable.name and (
                    not isinstance(variable.value, list)
                    or other_variable.value in variable.value
                ):
                    return other_variable

            # TODO: If variables are missing, we should prompt later.
            return variable

        return Variables(_override(variable) for variable in self.variables)


def find_template(path: Path) -> Optional[Path]:
    """Determine which child directory is the project template."""
    for item in path.iterdir():
        if "cookiecutter" in item.name and "{{" in item.name and "}}" in item.name:
            return item

    return None


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
        with path.open() as io:
            data = json.load(io)
        return cast(str, data["_template"])

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
    def location(self) -> str:
        """Return the template location."""
        return self.variables["_template"].value

    @property
    def extensions(self) -> List[str]:
        """Return the Jinja extensions."""
        return self.variables["_extensions"].value

    @property
    def copy_without_render(self) -> List[str]:
        """Return patterns for files to be copied without rendering."""
        return self.variables["_copy_without_render"].value

    def override(self, instance: Path) -> Template:
        """Override template configuration from an existing instance."""
        instance_variables = Variables.load(
            instance / ".cookiecutter.json", location=self.location
        )
        variables = self.variables.override(instance_variables)
        return replace(self, variables=variables)
