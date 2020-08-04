"""Prompt for user input."""
from typing import Any
from typing import cast
from typing import List

import click
from cookiecutter.environment import StrictEnvironment
from cookiecutter.exceptions import UndefinedVariableInTemplate
from cookiecutter.prompt import read_user_choice
from cookiecutter.prompt import read_user_dict
from jinja2.exceptions import UndefinedError

from .types import StrMapping


def read_user_variable(var_name: str, default_value: Any) -> Any:
    """Prompt user for variable and return the entered value or given default.

    Args:
        var_name: Variable of the context to query the user
        default_value: Value that will be returned if no input happens

    Returns:
        The entered value or given default.
    """
    # Please see https://click.palletsprojects.com/en/7.x/api/#click.prompt
    return click.prompt(var_name, default=default_value)


def render_variable(env: StrictEnvironment, value: Any, context: StrMapping) -> Any:
    """Render the next variable to be displayed in the user prompt.

    Inside the prompting taken from the cookiecutter.json file, this renders
    the next variable. For example, if a project_name is "Peanut Butter
    Cookie", the repo_name could be be rendered with:

        `{{ cookiecutter.project_name.replace(" ", "_") }}`.

    This is then presented to the user as the default.

    Args:
        env: A Jinja2 Environment object.
        value: The next value to be prompted for by the user.
        context: The current context as it's gradually being populated with variables.

    Returns:
        The rendered value for the default variable.
    """
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
    values: List[str],
    no_input: bool,
) -> str:
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
