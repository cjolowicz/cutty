"""Helper functions for contexts."""
import contextlib
import json
from pathlib import Path
from typing import Any
from typing import cast
from typing import Iterator
from typing import Tuple

from . import exceptions
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


def _override_context(context: Context, override: Context) -> Context:
    def _generate() -> Iterator[Tuple[str, Any]]:
        for key, value in context.items():
            try:
                yield key, _override_value(value, override[key])
            except KeyError:
                yield key, value

    return dict(_generate())
