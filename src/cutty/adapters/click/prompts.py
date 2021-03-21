"""Console prompts implemented using the click package."""
import json
from typing import Optional

import click

from cutty.domain.bindings import Value
from cutty.domain.bindings import ValueT
from cutty.domain.bindings import ValueT_co
from cutty.domain.bindings import ValueType
from cutty.domain.prompts import Prompt
from cutty.domain.prompts import PromptFactory
from cutty.domain.variables import Variable


class NoopPrompt(Prompt[ValueT_co]):
    """Return the default instead of prompting the user."""

    def promptvalue(self) -> ValueT_co:
        """Ask the user for a value."""
        return self.variable.default


class TextPrompt(Prompt[ValueT_co]):
    """Prompt for name and return the entered value or given default."""

    def promptvalue(self) -> ValueT_co:
        """Ask the user for a value."""
        # typeshed incorrectly requires Optional[str] for `default`
        value: ValueT_co = click.prompt(
            self.variable.name,
            default=self.variable.default,  # type: ignore[arg-type]
        )
        return value


class ChoicePrompt(Prompt[ValueT_co]):
    """Prompt to choose from several values for the given name."""

    def promptvalue(self) -> ValueT_co:
        """Ask the user for a value."""
        if not self.variable.choices:
            raise ValueError("variable with empty choices")

        choices = {
            str(number): value for number, value in enumerate(self.variable.choices, 1)
        }

        lines = [
            f"Select {self.variable.name}:",
            *[f"{number} - {value}" for number, value in choices.items()],
            "Choose from {}".format(", ".join(choices.keys())),
        ]

        choice = click.prompt(
            "\n".join(lines),
            type=click.Choice(choices.keys()),
            default="1",
            show_choices=False,
        )

        return choices[choice]


class JSONPrompt(Prompt[ValueT_co]):
    """Prompt to provide a dictionary of data."""

    def promptvalue(self) -> ValueT_co:
        """Ask the user for a value."""
        value: ValueT_co = click.prompt(
            self.variable.name,
            default="default",
            type=click.STRING,
            value_proc=_load_json_dict,
        )

        if value == "default":
            return self.variable.default

        return value


def _load_json_dict(value: Optional[str]) -> dict[str, Value]:
    """Load entered value as a JSON dict."""
    assert value is not None  # noqa: S101

    try:
        result: Value = json.loads(value)
    except Exception as error:
        raise click.UsageError(f"unable to decode to JSON: {error}")

    if not isinstance(result, dict):
        raise click.UsageError("requires JSON object")

    return result


class ClickPromptFactory(PromptFactory):
    """Given a variable, return a prompt."""

    def create(self, variable: Variable[ValueT]) -> Prompt[ValueT]:
        """Create a prompt."""
        if not variable.interactive:
            return NoopPrompt(variable)

        if variable.choices:
            return ChoicePrompt(variable)

        if variable.type is ValueType.OBJECT:
            return JSONPrompt(variable)

        return TextPrompt(variable)
