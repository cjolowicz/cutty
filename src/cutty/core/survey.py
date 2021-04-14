"""Survey."""
from typing import Any

from . import exceptions
from . import prompt
from .render import Renderer
from .template import Template
from .variables import Variable


class Survey:
    """Survey."""

    def __init__(
        self, template: Template, *, renderer: Renderer, interactive: bool = True
    ) -> None:
        """Initialize."""
        self.variables = sorted(
            template.variables, key=lambda variable: isinstance(variable.value, dict)
        )
        self.renderer = renderer
        self.interactive = interactive

    def run(self) -> None:
        """Bind variables from user input."""
        for variable in self.variables:
            value = self.ask(variable)
            self.renderer.bind(variable.name, value)

    def ask(self, variable: Variable) -> Any:
        """Return user input for a variable."""
        if variable.name.startswith("_"):
            return variable.value

        with exceptions.VariableRenderError(variable.name):
            value = self.renderer.render_json(variable.value)

        if not self.interactive:
            return value[0] if isinstance(variable.value, list) else value

        if isinstance(variable.value, list):
            return prompt.ask_choice(variable.name, values=value)

        if isinstance(variable.value, dict):
            return prompt.ask_json_dict(variable.name, default=value)

        return prompt.ask(variable.name, default=value)
