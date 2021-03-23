"""Filesystem-agnostic path."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar


PurePathT = TypeVar("PurePathT", bound="PurePath")


@dataclass
class PurePath:
    """Location in a filesystem."""

    parts: tuple[str, ...]

    def __init__(self, *parts: str) -> None:
        """Initialize."""
        object.__setattr__(self, "parts", parts)

    def _copy(self: PurePathT, path: PurePath) -> PurePathT:
        """Create a copy of the given path."""
        return self.__class__(*path.parts)

    def __str__(self) -> str:
        """Return a readable representation."""
        return "/".join(self.parts)

    def __truediv__(self: PurePathT, part: str) -> PurePathT:
        """Return a path with the part appended."""
        return self.joinpath(part)

    @property
    def name(self) -> str:
        """The final path component, if any."""
        return self.parts[-1] if self.parts else ""

    @property
    def stem(self) -> str:
        """The final path component, minus its last suffix."""
        name = self.name
        index = name.rfind(".")
        return name[:index] if 0 < index < len(name) - 1 else name

    @property
    def parent(self: PurePathT) -> PurePathT:
        """Return the parent of this path."""
        if not self.parts:
            return self

        path = PurePath(*self.parts[:-1])
        return self._copy(path)

    def joinpath(self: PurePathT, *parts: str) -> PurePathT:
        """Return a path with the parts appended."""
        path = PurePath(*self.parts, *parts)
        return self._copy(path)
