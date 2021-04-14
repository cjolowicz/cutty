"""Template variables."""
from __future__ import annotations

import contextlib
import json
from dataclasses import dataclass
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
    path: Path

    def as_string(self) -> str:
        """Check that the value is a string, and return it."""
        if not isinstance(self.value, str):
            raise exceptions.InvalidTemplateVariable(
                self.name, self.path.name, "str", repr(self.value)
            )

        return self.value

    def as_string_list(self) -> List[str]:
        """Check that the value is a list of strings, and return it."""
        if not (
            isinstance(self.value, list)
            and all(isinstance(item, str) for item in self.value)
        ):
            raise exceptions.InvalidTemplateVariable(
                self.name, self.path.name, "List[str]", repr(self.value)
            )

        return self.value


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

        variables = [Variable(name, value, path) for name, value in data.items()]

        for variable in variables:
            if isinstance(variable.value, list) and not variable.value:
                raise exceptions.InvalidTemplateVariable(
                    variable.name, path.name, "non-empty list", repr(variable.value)
                )

        return cls(variables, path=path)

    def __init__(self, variables: Iterable[Variable], *, path: Path) -> None:
        """Initialize."""
        self.variables = {variable.name: variable for variable in variables}
        self.path = path

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
        return Variable(name, default, self.path)

    @property
    def location(self) -> str:
        """Return the template location."""
        with exceptions.MissingTemplateVariable("_template", self.path.name):
            variable = self.variables["_template"]
        return variable.as_string()

    @property
    def extensions(self) -> List[str]:
        """Return the Jinja extensions."""
        variable = self.get("_extensions", default=[])
        return variable.as_string_list()

    @property
    def copy_without_render(self) -> List[str]:
        """Return patterns for files to be copied without rendering."""
        variable = self.get("_copy_without_render", default=[])
        return variable.as_string_list()

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

        return Variables([_override(variable) for variable in self], path=self.path)
