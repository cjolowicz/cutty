"""Cookiecutter loader."""
import json
from collections.abc import Iterator
from typing import Any

from cutty.filesystems.domain.path import Path
from cutty.templates.domain.config import Config
from cutty.templates.domain.variables import Variable


def loadvalue(value: Any) -> Any:
    """Stringize scalars."""
    if isinstance(value, (bool, int, float)):
        return str(value)

    if isinstance(value, (str, dict)):
        return value

    raise RuntimeError(f"unsupported value type {type(value)}")  # pragma: no cover


def loadvariable(name: str, value: Any) -> Variable:
    """Load a variable."""
    if isinstance(value, list):
        choices = tuple(loadvalue(choice) for choice in value)
        [valuetype] = set(type(choice) for choice in choices)
        return Variable(
            name=name,
            description=name,
            type=valuetype,
            default=choices[0],
            choices=choices,
            interactive=True,
        )

    value = loadvalue(value)
    return Variable(
        name=name,
        description=name,
        type=type(value),
        default=value,
        choices=(),
        interactive=True,
    )


def loadconfig(template: str, path: Path) -> Config:
    """Load the configurations for a Cookiecutter template."""
    text = (path / "cookiecutter.json").read_text()
    data = json.loads(text)

    assert isinstance(data, dict) and all(  # noqa: S101
        isinstance(name, str) for name in data
    )

    data.setdefault("_template", template)

    settings = dict(
        (name, value) for name, value in data.items() if name.startswith("_")
    )

    variables = tuple(
        loadvariable(name, value)
        for name, value in data.items()
        if not name.startswith("_")
    )

    return Config(settings, variables)


def loadpaths(path: Path, config: Config) -> Iterator[Path]:
    """Load project files in a Cookiecutter template."""
    for template_dir in path.iterdir():
        if all(token in template_dir.name for token in ("{{", "cookiecutter", "}}")):
            return iter([*loadhooks(path), template_dir])
    else:
        raise RuntimeError("template directory not found")  # pragma: no cover


def loadhooks(path: Path) -> Iterator[Path]:
    """Load hooks in a Cookiecutter template."""
    hookdir = path / "hooks"
    hooks = {"pre_gen_project", "post_gen_project"}

    if hookdir.is_dir():
        for path in hookdir.iterdir():
            if path.is_file() and not path.name.endswith("~") and path.stem in hooks:
                yield path
