"""Prompt for user input."""
from typing import Any
from typing import cast
from typing import List

import six
from cookiecutter.environment import StrictEnvironment
from cookiecutter.exceptions import UndefinedVariableInTemplate
from cookiecutter.prompt import read_user_choice
from cookiecutter.prompt import read_user_dict
from cookiecutter.prompt import read_user_variable
from jinja2.exceptions import UndefinedError

from .types import StrMapping


def render_variable(env: StrictEnvironment, value: Any, context: StrMapping) -> str:
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
    elif isinstance(value, dict):
        return {
            render_variable(env, k, context): render_variable(env, v, context)
            for k, v in value.items()
        }
    elif isinstance(value, list):
        return [render_variable(env, v, context) for v in value]
    elif not isinstance(value, six.string_types):
        value = str(value)

    template = env.from_string(value)

    rendered_template = template.render(cookiecutter=context)
    return rendered_template


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

    values: List[str] = [render_variable(env, value, context) for value in values]

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
