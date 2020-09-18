"""Template."""
from __future__ import annotations

import contextlib
import json
from dataclasses import dataclass
from dataclasses import replace
from pathlib import Path
from typing import Any
from typing import Iterable
from typing import Iterator
from typing import List
from typing import Optional

from . import exceptions
from .utils import with_context


@dataclass(frozen=True)
class Variable:
    """Template variable."""

    name: str
    value: Any


class Variables:
    """Collection of template variables."""

    @classmethod
    @with_context(
        lambda cls, path, **kwargs: (
            exceptions.TemplateConfigurationFileError(path.name),
            exceptions.TemplateConfigurationDoesNotExist(path.name).when(
                FileNotFoundError
            ),
            exceptions.InvalidTemplateConfiguration(path.name).when(
                json.decoder.JSONDecodeError
            ),
        )
    )
    def load(cls, path: Path, *, location: Optional[str] = None) -> Variables:
        """Load the template variables from a JSON file."""
        with path.open() as io:
            data = json.load(io)

        if not isinstance(data, dict):
            raise exceptions.TemplateConfigurationTypeError(
                path.name, "dict", type(data)
            )

        if location is not None:
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

    def get(self, name: str, *, default: Any = None) -> Variable:
        """Return the variable named `name`, or the provided default."""
        with contextlib.suppress(KeyError):
            return self.variables[name]
        return Variable(name, default)

    def override(self, other: Variables) -> Variables:
        """Override variables from another collection."""

        def _override(variable: Variable) -> Variable:
            if variable.name.startswith("_"):
                return variable

            for other_variable in other:
                if variable.name == other_variable.name and (
                    not isinstance(variable.value, list)
                    or other_variable.value in variable.value
                ):
                    return other_variable

            # TODO: If variables are missing, we should prompt later.
            return variable

        return Variables(_override(variable) for variable in self)


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
