"""Render."""
from pathlib import Path
from typing import Any
from typing import Dict

import jinja2

from . import extensions
from .template import Template


def create_environment(template: Template) -> jinja2.Environment:
    """Create the Jinja environment."""
    extensions_ = extensions.load(extra=template.extensions)
    return jinja2.Environment(  # noqa: S701
        loader=jinja2.FileSystemLoader(str(template.repository)),
        extensions=extensions_,
        keep_trailing_newline=True,
        undefined=jinja2.StrictUndefined,
    )


class Renderer:
    """Renderer."""

    def __init__(self, template: Template) -> None:
        """Initialize."""
        self.template = template
        self.context: Dict[str, Any] = {}
        self.environment = create_environment(template)

    def bind(self, name: str, value: Any) -> None:
        """Assign a value to a template variable."""
        self.context[name] = value

    def render(self, value: Any) -> Any:
        """Render a JSON value."""
        if isinstance(value, dict):
            return {self.render(key): self.render(val) for key, val in value.items()}

        if isinstance(value, list):
            return [self.render(item) for item in value]

        if isinstance(value, str):
            template = self.environment.from_string(value)
            return template.render(cookiecutter=self.context)

        if value is None:
            return None

        return str(value)

    def render_path(self, path: Path) -> str:
        """Render a file."""
        if path.is_absolute():
            path = path.relative_to(self.template.repository)

        template = self.environment.get_template(path.as_posix())
        return template.render(cookiecutter=self.context)
