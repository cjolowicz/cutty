"""Template."""
from __future__ import annotations

import json
from dataclasses import dataclass
from dataclasses import replace
from pathlib import Path
from typing import Any
from typing import List
from typing import Optional


DEFAULT_EXTENSIONS = [
    "cutty.common.extensions.JsonifyExtension",
    "cutty.common.extensions.RandomStringExtension",
    "cutty.common.extensions.SlugifyExtension",
    "jinja2_time.TimeExtension",
]


def find_template(path: Path) -> Path:
    """Determine which child directory is the project template."""
    for item in path.iterdir():
        if "cookiecutter" in item.name and "{{" in item.name and "}}" in item.name:
            return item
    else:
        raise Exception("template directory not found")


@dataclass(frozen=True)
class Variable:
    """Template variable."""

    name: str
    value: Any


@dataclass(frozen=True)
class Config:
    """Template configuration."""

    location: str
    variables: List[Variable]
    extensions: List[str]
    copy_without_render: List[str]

    @classmethod
    def load(cls, path: Path, *, location: Optional[str] = None) -> Config:
        """Load the template configuration."""
        with path.open() as io:
            data = json.load(io)
            location = data.setdefault("_template", location)
            assert location is not None  # noqa: S101  # TODO: raise

        variables = [Variable(name, value) for name, value in data.items()]
        extensions = DEFAULT_EXTENSIONS + data.get("_extensions", [])
        copy_without_render = data.get("_copy_without_render", [])

        return cls(location, variables, extensions, copy_without_render)

    def override(self, other: Config) -> Config:
        """Override variables from another configuration."""

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

        return replace(
            self, variables=[_override(variable) for variable in self.variables]
        )


@dataclass(frozen=True)
class Template:
    """Template."""

    root: Path
    config: Config

    @classmethod
    def load(
        cls, path: Path, *, location: str, overrides: Optional[Config] = None
    ) -> Template:
        """Load the template variables."""
        root = find_template(path)
        config = Config.load(path / "cookiecutter.json", location=location)
        if overrides is not None:
            config = config.override(overrides)

        return cls(root, config)
