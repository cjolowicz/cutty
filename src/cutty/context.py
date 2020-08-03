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
        with context_file.open() as file_handle:
            obj = json.load(file_handle)
    except ValueError as e:
        # JSON decoding error.  Let's throw a new exception that is more
        # friendly for the developer or user.
        full_fpath = context_file.resolve()
        json_exc_message = str(e)
        our_exc_message = (
            'JSON decoding error while loading "{0}".  Decoding'
            ' error details: "{1}"'.format(full_fpath, json_exc_message)
        )
        raise ContextDecodingException(our_exc_message)

    # Add the Python object to the context dictionary
    context = {context_file.stem: obj}

    # Overwrite context variable defaults with the default context from the
    # user's global config, if available
    if default_context:
        apply_overwrites_to_context(obj, default_context)
    if extra_context:
        apply_overwrites_to_context(obj, extra_context)

    logger.debug("Context generated is %s", context)

    context["cookiecutter"] = prompt_for_config(context, no_input)
    context["cookiecutter"]["_template"] = template

    return context
