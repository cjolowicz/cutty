"""Prompt for user input."""
from collections import OrderedDict

from cookiecutter.environment import StrictEnvironment
from cookiecutter.exceptions import UndefinedVariableInTemplate
from cookiecutter.prompt import prompt_choice_for_config
from cookiecutter.prompt import read_user_dict
from cookiecutter.prompt import read_user_variable
from cookiecutter.prompt import render_variable
from jinja2.exceptions import UndefinedError


def prompt_for_config(context, no_input=False):  # noqa: C901
    """Prompt user to enter a new config.

    :param dict context: Source for field names and sample values.
    :param no_input: Prompt the user at command line for manual configuration?
    """
    cookiecutter_dict = OrderedDict([])
    env = StrictEnvironment(context=context)

    # First pass: Handle simple and raw variables, plus choices.
    # These must be done first because the dictionaries keys and
    # values might refer to them.
    for key, raw in context[u"cookiecutter"].items():
        if key.startswith(u"_"):
            cookiecutter_dict[key] = raw
            continue

        try:
            if isinstance(raw, list):
                # We are dealing with a choice variable
                val = prompt_choice_for_config(
                    cookiecutter_dict, env, key, raw, no_input
                )
                cookiecutter_dict[key] = val
            elif not isinstance(raw, dict):
                # We are dealing with a regular variable
                val = render_variable(env, raw, cookiecutter_dict)

                if not no_input:
                    val = read_user_variable(key, val)

                cookiecutter_dict[key] = val
        except UndefinedError as err:
            msg = "Unable to render variable '{}'".format(key)
            raise UndefinedVariableInTemplate(msg, err, context)

    # Second pass; handle the dictionaries.
    for key, raw in context[u"cookiecutter"].items():

        try:
            if isinstance(raw, dict):
                # We are dealing with a dict variable
                val = render_variable(env, raw, cookiecutter_dict)

                if not no_input:
                    val = read_user_dict(key, val)

                cookiecutter_dict[key] = val
        except UndefinedError as err:
            msg = "Unable to render variable '{}'".format(key)
            raise UndefinedVariableInTemplate(msg, err, context)

    return cookiecutter_dict
