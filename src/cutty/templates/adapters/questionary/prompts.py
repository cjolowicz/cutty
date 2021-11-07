"""Prompts using questionary."""
import json
from typing import Any

import questionary
from prompt_toolkit.document import Document
from prompt_toolkit.lexers import PygmentsLexer
from pygments.lexers.data import JsonLexer
from questionary import ValidationError
from questionary import Validator

from cutty.templates.domain.binders import bind
from cutty.templates.domain.binders import binddefault
from cutty.templates.domain.binders import Binder
from cutty.templates.domain.bindings import Binding
from cutty.templates.domain.variables import Variable


def _load_json_dict(value: str) -> dict[str, Any]:
    """Load entered value as a JSON dict."""
    try:
        result = json.loads(value)
    except Exception as error:
        raise ValueError(f"unable to decode to JSON: {error}")

    if not isinstance(result, dict):
        raise ValueError("requires JSON object")

    return result


class _JSONValidator(Validator):
    def validate(self, document: Document) -> None:
        try:
            _load_json_dict(document.text)
        except ValueError as error:
            raise ValidationError(
                message=str(error), cursor_position=len(document.text)
            )


def createprompt(*, input: Any = None, output: Any = None) -> Binder:
    """Create a prompt."""

    def prompt(variable: Variable) -> Binding:
        """Bind a variable by prompting."""
        if not variable.interactive:
            return binddefault(variable)

        if issubclass(variable.type, dict):
            default = json.dumps(variable.default, indent=2)
            question = questionary.text(
                variable.name,
                default=default,
                validate=_JSONValidator,
                lexer=PygmentsLexer(JsonLexer),
                multiline=True,
                input=input,
                output=output,
            )

            return bind(variable, _load_json_dict(question.ask()))

        if variable.choices:
            question = questionary.select(
                variable.name,
                choices=variable.choices,
                default=variable.default,
                use_shortcuts=True,
                input=input,
                output=output,
            )
        else:
            question = questionary.text(
                variable.name, default=variable.default, input=input, output=output
            )

        value: str = question.ask()

        return bind(variable, value)

    return prompt


if __name__ == "__main__":  # pragma: no cover
    from cutty.templates.domain.variables import GenericVariable

    name, default = "metadata", {"name": "example"}
    variable = GenericVariable(name, name, type(default), default, (), True)

    prompt = createprompt()
    binding = prompt(variable)

    print(binding)
