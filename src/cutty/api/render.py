"""Render."""
from pathlib import Path
from typing import Any
from typing import Dict

import jinja2

from .template import Template


class Renderer:
    """Renderer."""

    def __init__(self, template: Template) -> None:
        """Initialize."""
        self.template = template
        self.context: Dict[str, Any] = {}
        self.environment = jinja2.Environment(  # noqa: S701
            loader=jinja2.FileSystemLoader(str(template.root)),
            extensions=template.extensions,
            keep_trailing_newline=True,
            undefined=jinja2.StrictUndefined,
        )

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
            path = path.relative_to(self.template.root)

        template = self.environment.get_template(path.as_posix())
        return template.render(cookiecutter=self.context)
