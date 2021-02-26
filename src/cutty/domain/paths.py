"""Paths."""
from collections.abc import Iterable
from dataclasses import dataclass


class EmptyPathComponent(Exception):
    """The rendered path has an empty component."""


class InvalidPathComponent(Exception):
    """The rendered path has an invalid component."""


@dataclass(frozen=True)
class Path:
    """The location of a file within a template or project."""

    parts: tuple[str, ...]

    @classmethod
    def fromparts(cls, parts: Iterable[str]) -> Path:
        """Create a Path from parts."""
        parts = tuple(parts)

        for part in parts:
            if not part:
                raise EmptyPathComponent(parts, part)

            if "/" in part or "\\" in part or part == "." or part == "..":
                raise InvalidPathComponent(parts, part)

        return cls(parts)
