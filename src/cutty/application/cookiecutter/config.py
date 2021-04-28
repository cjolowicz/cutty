"""Cookiecutter loader."""
import json
from typing import Any
from typing import Optional

from cutty.filesystems.domain.path import Path
from cutty.plugins.domain.hooks import implements
from cutty.plugins.domain.registry import Registry
from cutty.templates.adapters.hooks import loadtemplateconfig
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


def registerconfigloader(registry: Registry, template: str) -> None:
    """Register a loader for Cookiecutter template configurations."""

    @registry.register
    @implements(loadtemplateconfig)
    def loadtemplateconfig_impl(path: Path) -> Optional[Config]:
        """Load the configuration for a Cookiecutter template."""
        text = (path / "cookiecutter.json").read_text()
        data = json.loads(text)

        assert isinstance(data, dict) and all(  # noqa: S101
            isinstance(name, str) for name in data
        )

        data.setdefault("_template", template)

        settings = {name: value for name, value in data.items() if name.startswith("_")}

        variables = tuple(
            loadvariable(name, value)
            for name, value in data.items()
            if not name.startswith("_")
        )

        return Config(settings, variables)
