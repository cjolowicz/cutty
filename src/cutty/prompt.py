"""Prompt for user input."""
import json
from typing import Any
from typing import cast
from typing import Dict
from typing import List
from typing import Optional

import click
from cookiecutter.environment import StrictEnvironment
from cookiecutter.exceptions import UndefinedVariableInTemplate
from jinja2.exceptions import UndefinedError

from .types import StrMapping


def read_user_variable(variable: str, default: Any) -> Any:
    """Prompt user for variable and return the entered value or given default."""
    return click.prompt(variable, default=default)


def read_user_choice(variable: str, values: List[Any]) -> Any:
    """Prompt the user to choose from several values for the given variable."""
    if not values:
        raise ValueError

    choices = {str(number): value for number, value in enumerate(values, 1)}
    numbers = choices.keys()
    prompt = "\n".join(
        [
            f"Select {variable}:",
            *[f"{number} - {value}" for number, value in choices.items()],
            "Choose from {}".format(", ".join(numbers)),
        ]
    )
    choice = click.prompt(
        prompt, type=click.Choice(numbers), default="1", show_choices=False
    )

    return choices[choice]


def read_user_dict(variable: str, default: Dict[Any, Any]) -> Dict[Any, Any]:
    """Prompt the user to provide a dictionary of data."""
    if not isinstance(default, dict):
        raise TypeError

    value = click.prompt(
        variable, default="default", type=click.STRING, value_proc=load_json_dict
    )

    return cast(Dict[Any, Any], value) if value != "default" else default


def load_json_dict(value: Optional[str]) -> Any:
    """Load user-supplied value as a JSON dict."""
    assert value is not None  # noqa: S101
    try:
        result = json.loads(value)
    except Exception:
        raise click.UsageError("Unable to decode to JSON.")

    if not isinstance(result, dict):
        raise click.UsageError("Requires JSON dict.")

    return result


def render_variable(env: StrictEnvironment, value: Any, context: StrMapping) -> Any:
    """Render the next variable to be displayed in the user prompt."""
    if value is None:
        return None

    if isinstance(value, dict):
        return {
            render_variable(env, key, context): render_variable(env, val, context)
            for key, val in value.items()
        }

    if isinstance(value, list):
        return [render_variable(env, item, context) for item in value]

    template = env.from_string(str(value))

    return template.render(cookiecutter=context)


def prompt_choice_for_config(
    context: StrMapping,
    env: StrictEnvironment,
    key: str,
    values: List[Any],
    no_input: bool,
) -> Any:
    """Prompt user with a set of values to choose from.

    Each of the possible choices is rendered beforehand.
    """
    if no_input:
        return cast(str, render_variable(env, values[0], context))

    values = render_variable(env, values, context)

    return cast(str, read_user_choice(key, values))


def prompt_for_config(  # noqa: C901
    context: StrMapping, *, no_input: bool = False
) -> StrMapping:
    """Prompt user to enter a new config.

    Args:
        context: Source for field names and sample values (the object under
            the "cookiecutter" key).  # noqa: RST203
        no_input: Prompt the user at command line for manual configuration?

    Returns:
        The generated context (the object under the "cookiecutter" key).

    Raises:
        UndefinedVariableInTemplate: Cannot render a template variable.
    """
    result = {}
    env = StrictEnvironment(context={"cookiecutter": context})

    # First pass: Handle simple and raw variables, plus choices.
    # These must be done first because the dictionaries keys and
    # values might refer to them.
    for key, value in context.items():
        if key.startswith("_"):
            result[key] = value
            continue

        try:
            if isinstance(value, list):
                # We are dealing with a choice variable
                result[key] = prompt_choice_for_config(
                    result, env, key, value, no_input
                )
            elif not isinstance(value, dict):
                # We are dealing with a regular variable
                value = render_variable(env, value, result)

                if not no_input:
                    value = read_user_variable(key, value)

                result[key] = value
        except UndefinedError as error:
            raise UndefinedVariableInTemplate(
                f"Unable to render variable {key!r}", error, {"cookiecutter": context}
            )

    # Second pass; handle the dictionaries.
    for key, value in context.items():
        try:
            if isinstance(value, dict):
                # We are dealing with a dict variable
                value = render_variable(env, value, result)

                if not no_input:
                    value = read_user_dict(key, value)

                result[key] = value
        except UndefinedError as error:
            raise UndefinedVariableInTemplate(
                f"Unable to render variable {key!r}", error, {"cookiecutter": context}
            )

    return result
