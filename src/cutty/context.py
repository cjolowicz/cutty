"""Helper functions for contexts."""
import contextlib
import json
from pathlib import Path
from typing import Any
from typing import cast
from typing import Optional

from cookiecutter.exceptions import ContextDecodingException
from cookiecutter.prompt import prompt_for_config

from .types import MutableStrMapping
from .types import StrMapping


def load_context(
    context_file: Path, *, default: Optional[StrMapping] = None
) -> StrMapping:
    """Load context from disk."""
    if default is not None and not context_file.exists():
        return default

    try:
        with context_file.open() as io:
            return cast(StrMapping, json.load(io))
    except ValueError as error:
        raise ContextDecodingException(
            "JSON decoding error while loading '{}'."
            "  Decoding error details: '{}'".format(context_file.resolve(), error)
        )


def _override_value(value: Any, other: Any) -> Any:
    if isinstance(value, list):
        with contextlib.suppress(ValueError):
            # Set other as default for the choice variable.
            value.remove(other)
            return [other, *value]
        return value
    return other


def _override_context(context: MutableStrMapping, *others: StrMapping) -> None:
    for other in others:
        for variable, override in other.items():
            with contextlib.suppress(KeyError):
                context[variable] = _override_value(context[variable], override)


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
    try:
        with context_file.open() as io:
            data = json.load(io)
    except ValueError as error:
        raise ContextDecodingException(
            "JSON decoding error while loading '{}'."
            "  Decoding error details: '{}'".format(context_file.resolve(), error)
        )

    _override_context(data, default_context, extra_context)

    context = {"cookiecutter": data}

    data = prompt_for_config(context, no_input)
    data["_template"] = template

    return context
