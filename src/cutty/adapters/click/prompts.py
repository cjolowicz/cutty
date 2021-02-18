"""Console prompts implemented using the click package."""
import json
from typing import Optional

import click

from cutty.domain.prompts import Prompt
from cutty.domain.prompts import PromptFactory
from cutty.domain.variables import Value
from cutty.domain.variables import ValueT
from cutty.domain.variables import ValueT_co
from cutty.domain.varspecs import VariableSpecification
from cutty.domain.varspecs import VariableType


class NoopPrompt(Prompt[ValueT_co]):
    """Return the default instead of prompting the user."""

    def promptvalue(self) -> ValueT_co:
        """Ask the user for a value."""
        return self.specification.default


class TextPrompt(Prompt[ValueT_co]):
    """Prompt for name and return the entered value or given default."""

    def promptvalue(self) -> ValueT_co:
        """Ask the user for a value."""
        # typeshed incorrectly requires Optional[str] for `default`
        value: ValueT_co = click.prompt(
            self.specification.name,
            default=self.specification.default,  # type: ignore[arg-type]
        )
        return value


class ChoicePrompt(Prompt[ValueT_co]):
    """Prompt to choose from several values for the given name."""

    def promptvalue(self) -> ValueT_co:
        """Ask the user for a value."""
        if not self.specification.choices:
            raise ValueError("variable specification with empty choices")

        choices = {
            str(number): value
            for number, value in enumerate(self.specification.choices, 1)
        }

        lines = [
            f"Select {self.specification.name}:",
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
            self.specification.name,
            default="default",
            type=click.STRING,
            value_proc=_load_json_dict,
        )

        if value == "default":
            return self.specification.default

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
    """Given a variable specification, return a prompt."""

    def create(self, specification: VariableSpecification[ValueT]) -> Prompt[ValueT]:
        """Create a prompt."""
        if not specification.interactive:
            return NoopPrompt(specification)

        if specification.choices:
            return ChoicePrompt(specification)

        if specification.type is VariableType.OBJECT:
            return JSONPrompt(specification)

        return TextPrompt(specification)
