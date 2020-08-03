"""Helper functions for contexts."""
import json
import logging
from pathlib import Path
from typing import cast
from typing import Optional

from cookiecutter.exceptions import ContextDecodingException
from cookiecutter.prompt import prompt_for_config

from .types import MutableStrMapping
from .types import StrMapping


logger = logging.getLogger(__name__)


def load_context(
    context_file: Path, *, default: Optional[StrMapping] = None
) -> StrMapping:
    """Load context from disk."""
    if default is not None and not context_file.exists():
        return default
    with context_file.open() as io:
        return cast(StrMapping, json.load(io))


def apply_override_to_context(
    context: MutableStrMapping, override_context: StrMapping
) -> None:
    """Modify the given context in place based on the override_context."""
    for variable, override in override_context.items():
        if variable not in context:
            # Do not include variables which are not used in the template
            continue

        context_value = context[variable]

        if isinstance(context_value, list):
            # We are dealing with a choice variable
            if override in context_value:
                # This override is actually valid for the given context
                # Let's set it as default (by definition first item in list)
                # see ``cookiecutter.prompt.prompt_choice_for_config``
                context_value.remove(override)
                context_value.insert(0, override)
        else:
            # Simply override the value for this variable
            context[variable] = override


def create_context(
    context_file: Path,
    *,
    template: str,
    extra_context: StrMapping,
    no_input: bool,
    default_context: StrMapping,
) -> StrMapping:
    """Generate the context for a Cookiecutter project template.

    Loads the JSON file as a Python object, with key being the JSON filename.

    Args:
        context_file: JSON file containing key/value pairs for populating
            the cookiecutter's variables.  # noqa: RST203
        template: Project template location
        extra_context: Dictionary containing configuration overrides
        no_input: If True, do not ask for user input.
        default_context: Dictionary containing config to take into account.

    Returns:
        The generated context.

    Raises:
        ContextDecodingException: The JSON file is invalid.
    """
    logger.debug("context_file is %s", context_file)

    try:
        with context_file.open() as io:
            data = json.load(io)
    except ValueError as error:
        raise ContextDecodingException(
            "JSON decoding error while loading '{}'."
            "  Decoding error details: '{}'".format(context_file.resolve(), error)
        )

    if default_context:
        apply_override_to_context(data, default_context)

    if extra_context:
        apply_override_to_context(data, extra_context)

    context = {"cookiecutter": data}

    logger.debug("Context generated is %s", context)

    data = prompt_for_config(context, no_input)
    data["_template"] = template

    return context
