"""Template."""
from __future__ import annotations

import json
from dataclasses import dataclass
from dataclasses import replace
from pathlib import Path
from typing import Optional

from . import exceptions
from .utils import with_context
from .variables import Variables


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

    @classmethod
    def load(cls, path: Path, *, version: str, location: str) -> Template:
        """Load the template variables."""
        root = find_template(path)
        if root is None:
            raise exceptions.TemplateDirectoryNotFound(location)

        hookdir = path / "hooks"
        variables = cls.load_variables(path / "cookiecutter.json", location=location)

        return cls(
            root=root,
            hookdir=hookdir,
            repository=path,
            version=version,
            variables=variables,
        )

    @classmethod
    def load_location(cls, instance: Path) -> str:
        """Return the location specified in the given instance."""
        path = instance / ".cookiecutter.json"
        variables = cls.load_variables(path)

        with exceptions.MissingTemplateVariable("_template", path).when(KeyError):
            location = variables["_template"].value

        if not isinstance(location, str):
            raise exceptions.InvalidTemplateVariable(
                "_template", path, "str", repr(location)
            )

        return location

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
    def load_variables(cls, path: Path, *, location: Optional[str] = None) -> Variables:
        """Load the template variables from a JSON file."""
        with path.open() as io:
            data = json.load(io)

        if not isinstance(data, dict):
            raise exceptions.TemplateConfigurationTypeError(
                path.name, "dict", type(data)
            )

        if location is not None:
            data["_template"] = location

        variables = Variables.fromdict(data)

        for variable in variables:
            if isinstance(variable.value, list) and not variable.value:
                raise exceptions.InvalidTemplateVariable(
                    variable.name, path.name, "non-empty list", repr(variable.value)
                )

        return variables

    def override(self, instance: Path) -> Template:
        """Override template configuration from an existing instance."""
        instance_variables = self.load_variables(instance / ".cookiecutter.json")
        variables = self.variables.override(instance_variables)
        return replace(self, variables=variables)
