"""Template variables."""
from __future__ import annotations

import contextlib
from dataclasses import dataclass
from typing import Any
from typing import Iterable
from typing import Iterator
from typing import List
from typing import Mapping

from . import exceptions


@dataclass(frozen=True)
class Variable:
    """Template variable."""

    name: str
    value: Any


def as_string_list(variable: Variable) -> List[str]:
    """Check that the value is a list of strings, and return it."""
    if not (
        isinstance(variable.value, list)
        and all(isinstance(item, str) for item in variable.value)
    ):
        raise exceptions.InvalidTemplateVariable(
            variable.name, "cookiecutter.json", "List[str]", repr(variable.value)
        )

    return variable.value


class Variables:
    """Collection of template variables."""

    @classmethod
    def fromdict(cls, data: Mapping[str, Any]) -> Variables:
        """Create variables from a dictionary or another mapping."""
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

    @property
    def extensions(self) -> List[str]:
        """Return the Jinja extensions."""
        variable = self.get("_extensions", default=[])
        return as_string_list(variable)

    @property
    def copy_without_render(self) -> List[str]:
        """Return patterns for files to be copied without rendering."""
        variable = self.get("_copy_without_render", default=[])
        return as_string_list(variable)

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
