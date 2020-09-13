"""Survey."""
from typing import Any
from typing import List

from . import exceptions
from . import prompt
from .render import Renderer
from .template import Variable


class Survey:
    """Survey."""

    def __init__(self, variables: List[Variable], *, interactive: bool = True) -> None:
        """Initialize."""
        self.variables = variables
        self.variables.sort(key=lambda variable: isinstance(variable.value, dict))
        self.interactive = interactive

    def run(self, renderer: Renderer) -> None:
        """Bind variables from user input."""
        for variable in self.variables:
            value = self.run_one(renderer, variable)
            renderer.bind(variable.name, value)

    def run_one(self, renderer: Renderer, variable: Variable) -> Any:
        """Return user input for a variable."""
        if variable.name.startswith("_"):
            return variable.value

        with exceptions.VariableRenderError(variable.name):
            value = renderer.render(variable.value)

        if not self.interactive:
            return value[0] if isinstance(variable.value, list) else value

        if isinstance(variable.value, list):
            return prompt.ask_choice(variable.name, values=value)

        if isinstance(variable.value, dict):
            return prompt.ask_json_dict(variable.name, default=value)

        return prompt.ask(variable.name, default=value)
