"""Template."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import List


DEFAULT_EXTENSIONS = [
    "cutty.extensions.JsonifyExtension",
    "cutty.extensions.RandomStringExtension",
    "cutty.extensions.SlugifyExtension",
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
class Template:
    """Template."""

    root: Path
    variables: List[Variable]
    extensions: List[str]
    copy_without_render: List[str]

    @classmethod
    def load(cls, path: Path, *, location: str) -> Template:
        """Load the template variables."""
        with (path / "cookiecutter.json").open() as io:
            data = json.load(io)
            data.setdefault("_template", location)

        root = find_template(path)
        variables = [Variable(name, value) for name, value in data.items()]
        extensions = DEFAULT_EXTENSIONS + data.get("_extensions", [])
        copy_without_render = data.get("_copy_without_render", [])

        return cls(root, variables, extensions, copy_without_render)
