"""Helper functions for contexts."""
import contextlib
import json
from collections import ChainMap
from pathlib import Path
from typing import Any
from typing import cast
from typing import Iterator
from typing import Tuple

from . import exceptions
from .prompt import prompt_for_config
from .types import Context


class Store:
    """File-based storage for context."""

    def __init__(self, path: Path) -> None:
        """Initialize."""
        self.path = path

    def load(self) -> Context:
        """Load the context."""
        with self.path.open() as io:
            try:
                context = json.load(io)
            except ValueError as error:
                raise exceptions.ContextDecodingException(
                    f"JSON decoding error while loading '{self.path.resolve()}'."
                    f"  Decoding error details: '{error}'"
                )

        return cast(Context, context)

    def dump(self, context: Context) -> None:
        """Dump the context."""
        with self.path.open(mode="w") as io:
            json.dump(context, io, indent=2)


def _override_value(value: Any, other: Any) -> Any:
    if isinstance(value, list):
        with contextlib.suppress(ValueError):
            # Set other as default for the choice variable.
            value.remove(other)
            return [other, *value]
        return value
    return other


def _override_context(context: Context, *overrides: Context) -> Context:
    override = ChainMap(*reversed(overrides))

    def _generate() -> Iterator[Tuple[str, Any]]:
        for key, value in context.items():
            try:
                yield key, _override_value(value, override[key])
            except KeyError:
                yield key, value

    return dict(_generate())


def create_context(
    store: Store,
    *,
    template: str,
    extra_context: Context,
    no_input: bool,
    default_context: Context,
) -> Context:
    """Generate the context for a Cookiecutter project template."""
    context = store.load()
    context = _override_context(context, default_context, extra_context)
    context = prompt_for_config(context, no_input=no_input)

    return {**context, "_template": template}
