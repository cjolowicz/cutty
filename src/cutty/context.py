"""Helper functions for contexts."""
import contextlib
import json
from collections import ChainMap
from pathlib import Path
from typing import Any
from typing import cast
from typing import Iterator
from typing import Optional
from typing import Tuple

from cookiecutter.exceptions import ContextDecodingException
from cookiecutter.prompt import prompt_for_config

from .types import StrMapping


def load_context(path: Path, *, default: Optional[StrMapping] = None) -> StrMapping:
    """Load context from disk."""
    if default is not None and not path.exists():
        return default

    try:
        with path.open() as io:
            return cast(StrMapping, json.load(io))
    except ValueError as error:
        raise ContextDecodingException(
            "JSON decoding error while loading '{}'."
            "  Decoding error details: '{}'".format(path.resolve(), error)
        )


def _override_value(value: Any, other: Any) -> Any:
    if isinstance(value, list):
        with contextlib.suppress(ValueError):
            # Set other as default for the choice variable.
            value.remove(other)
            return [other, *value]
        return value
    return other


def _override_context(context: StrMapping, *others: StrMapping) -> StrMapping:
    def _generate() -> Iterator[Tuple[str, Any]]:
        other = ChainMap(*reversed(others))
        for key, value in context.items():
            try:
                yield key, _override_value(value, other[key])
            except KeyError:
                yield key, value

    return dict(_generate())


def create_context(
    path: Path,
    *,
    template: str,
    extra_context: StrMapping,
    no_input: bool,
    default_context: StrMapping,
) -> StrMapping:
    """Generate the context for a Cookiecutter project template.

    Loads the JSON file as a Python object, with key being the JSON filename.

    Args:
        path: JSON file containing key/value pairs for populating
            the cookiecutter's variables.  # noqa: RST203
        template: Project template location
        extra_context: Dictionary containing configuration overrides
        no_input: If True, do not ask for user input.
        default_context: Dictionary containing config to take into account.

    Returns:
        The generated context.
    """
    data = load_context(path)
    data = _override_context(data, default_context, extra_context)
    data = prompt_for_config({"cookiecutter": data}, no_input)

    return {"cookiecutter": {**data, "_template": template}}
