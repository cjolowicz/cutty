"""Helper functions for contexts."""
from __future__ import annotations

import contextlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import Iterator
from typing import Tuple

from ..common.types import Context as _Context


@dataclass
class Context:
    """A collection of template variables."""

    data: _Context

    @classmethod
    def load(cls, path: Path) -> Context:
        """Load the context."""
        with path.open() as io:
            return cls(json.load(io))

    def dump(self, path: Path) -> None:
        """Dump the context."""
        with path.open(mode="w") as io:
            json.dump(self.data, io, indent=2)


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
