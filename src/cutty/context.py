"""Helper functions for contexts."""
import contextlib
import json
from pathlib import Path
from typing import Any
from typing import cast
from typing import Iterator
from typing import Tuple

from . import exceptions
from .types import Context as _Context


class Store:
    """File-based storage for context."""

    def __init__(self, path: Path) -> None:
        """Initialize."""
        self.path = path

    def load(self) -> _Context:
        """Load the context."""
        with self.path.open() as io:
            try:
                context = json.load(io)
            except ValueError as error:
                raise exceptions.ContextDecodingException(
                    f"JSON decoding error while loading '{self.path.resolve()}'."
                    f"  Decoding error details: '{error}'"
                )

        return cast(_Context, context)

    def dump(self, context: _Context) -> None:
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


def override_context(context: _Context, override: _Context) -> _Context:
    """Override entries in a context."""

    def _generate() -> Iterator[Tuple[str, Any]]:
        for key, value in context.items():
            with contextlib.suppress(KeyError):
                value = _override_value(value, override[key])
            yield key, value

    return dict(_generate())
