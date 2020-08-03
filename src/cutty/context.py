"""Helper functions for contexts."""
import json
import logging
from pathlib import Path
from typing import cast
from typing import Optional

from cookiecutter.exceptions import ContextDecodingException
from cookiecutter.generate import apply_overwrites_to_context
from cookiecutter.prompt import prompt_for_config

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
        apply_overwrites_to_context(data, default_context)

    if extra_context:
        apply_overwrites_to_context(data, extra_context)

    context = {"cookiecutter": data}

    logger.debug("Context generated is %s", context)

    data = prompt_for_config(context, no_input)
    data["_template"] = template

    return context
