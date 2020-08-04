"""Prompt for user input."""
from collections import OrderedDict

from cookiecutter.environment import StrictEnvironment
from cookiecutter.exceptions import UndefinedVariableInTemplate
from cookiecutter.prompt import prompt_choice_for_config
from cookiecutter.prompt import read_user_dict
from cookiecutter.prompt import read_user_variable
from cookiecutter.prompt import render_variable
from jinja2.exceptions import UndefinedError

from .types import StrMapping


def prompt_for_config(  # noqa: C901
    context: StrMapping, *, no_input: bool = False
) -> StrMapping:
    """Prompt user to enter a new config.

    Args:
        context: Source for field names and sample values.
        no_input: Prompt the user at command line for manual configuration?

    Returns:
        The generated context (the object under the "cookiecutter" key).

    Raises:
        UndefinedVariableInTemplate: Cannot render a template variable.
    """
    result = OrderedDict([])
    env = StrictEnvironment(context=context)

    # First pass: Handle simple and raw variables, plus choices.
    # These must be done first because the dictionaries keys and
    # values might refer to them.
    for key, raw in context["cookiecutter"].items():
        if key.startswith("_"):
            result[key] = raw
            continue

        try:
            if isinstance(raw, list):
                # We are dealing with a choice variable
                val = prompt_choice_for_config(result, env, key, raw, no_input)
                result[key] = val
            elif not isinstance(raw, dict):
                # We are dealing with a regular variable
                val = render_variable(env, raw, result)

                if not no_input:
                    val = read_user_variable(key, val)

                result[key] = val
        except UndefinedError as err:
            msg = "Unable to render variable '{}'".format(key)
            raise UndefinedVariableInTemplate(msg, err, context)

    # Second pass; handle the dictionaries.
    for key, raw in context["cookiecutter"].items():

        try:
            if isinstance(raw, dict):
                # We are dealing with a dict variable
                val = render_variable(env, raw, result)

                if not no_input:
                    val = read_user_dict(key, val)

                result[key] = val
        except UndefinedError as err:
            msg = "Unable to render variable '{}'".format(key)
            raise UndefinedVariableInTemplate(msg, err, context)

    return result
