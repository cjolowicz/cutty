"""Console prompts implemented using the click package."""
import json
from typing import Optional

import click

from cutty.domain.binders import bind
from cutty.domain.binders import binddefault
from cutty.domain.bindings import Binding
from cutty.domain.values import Value
from cutty.domain.values import ValueType
from cutty.domain.variables import Variable


def textprompt(variable: Variable) -> Binding:
    """Prompt for name and return the entered value or given default."""
    # typeshed incorrectly requires Optional[str] for `default`
    value: Value = click.prompt(
        variable.name,
        default=variable.default,  # type: ignore[arg-type]
    )
    return bind(variable, value)


def choiceprompt(variable: Variable) -> Binding:
    """Prompt to choose from several values for the given name."""
    if not variable.choices:
        raise ValueError("variable with empty choices")

    choices = {str(number): value for number, value in enumerate(variable.choices, 1)}

    lines = [
        f"Select {variable.name}:",
        *[f"{number} - {value}" for number, value in choices.items()],
        "Choose from {}".format(", ".join(choices.keys())),
    ]

    choice = click.prompt(
        "\n".join(lines),
        type=click.Choice(choices.keys()),
        default="1",
        show_choices=False,
    )

    return bind(variable, choices[choice])


def jsonprompt(variable: Variable) -> Binding:
    """Prompt to provide a dictionary of data."""
    value: Value = click.prompt(
        variable.name,
        default="default",
        type=click.STRING,
        value_proc=_load_json_dict,
    )

    if value == "default":
        return binddefault(variable)

    return bind(variable, value)


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


def prompt(variable: Variable) -> Binding:
    """Bind a variable by prompting."""
    if not variable.interactive:
        return binddefault(variable)

    if variable.choices:
        return choiceprompt(variable)

    if variable.type is ValueType.OBJECT:
        return jsonprompt(variable)

    return textprompt(variable)
