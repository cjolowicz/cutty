"""Prompt for user input."""
from typing import cast
from typing import List

from cookiecutter.environment import StrictEnvironment
from cookiecutter.exceptions import UndefinedVariableInTemplate
from cookiecutter.prompt import read_user_choice
from cookiecutter.prompt import read_user_dict
from cookiecutter.prompt import read_user_variable
from cookiecutter.prompt import render_variable
from jinja2.exceptions import UndefinedError

from .types import StrMapping


def prompt_choice_for_config(
    context: StrMapping,
    env: StrictEnvironment,
    key: str,
    options: List[str],
    no_input: bool,
) -> str:
    """Prompt user with a set of options to choose from.

    Each of the possible choices is rendered beforehand.
    """
    rendered_options: List[str] = [
        render_variable(env, raw, context) for raw in options
    ]

    if no_input:
        return rendered_options[0]
    return cast(str, read_user_choice(key, rendered_options))


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
