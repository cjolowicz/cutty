"""Filesystem-agnostic path."""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import overload
from typing import TypeVar
from typing import Union


PurePathT = TypeVar("PurePathT", bound="PurePath")


@dataclass(frozen=True)
class PurePath:
    """Location in a filesystem."""

    parts: tuple[str, ...]

    def __init__(self, *parts: str) -> None:
        """Initialize."""
        object.__setattr__(self, "parts", parts)

    def _withparts(self: PurePathT, *parts: str) -> PurePathT:
        """Create a path with the given parts."""
        return self.__class__(*parts)

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
        return self._withparts(*self.parts[:-1]) if self.parts else self

    @property
    def parents(self: PurePathT) -> Sequence[PurePathT]:
        """Return the ancestors of the path."""
        return Parents(self)

    def joinpath(self: PurePathT, *parts: str) -> PurePathT:
        """Return a path with the parts appended."""
        return self._withparts(*self.parts, *parts)


class Parents(Sequence[PurePathT]):
    """Sequence-like access to the logical ancestors of a path."""

    def __init__(self, path: PurePathT) -> None:
        """Initialize."""
        self.path = path

    def __len__(self) -> int:
        """Return the number of parents."""
        return len(self.path.parts)

    @overload
    def __getitem__(self, index: int) -> PurePathT:  # noqa: D105
        ...

    @overload
    def __getitem__(self, index: slice) -> Sequence[PurePathT]:  # noqa: D105
        ...

    def __getitem__(
        self, index: Union[int, slice]
    ) -> Union[PurePathT, Sequence[PurePathT]]:
        """Return the nth parent."""
        if isinstance(index, slice):
            indices = index.indices(len(self))
            return tuple(self[index] for index in range(*indices))

        if index >= len(self) or index < -len(self):
            raise IndexError(index)

        parts = self.path.parts[: -(index + 1)]
        return self.path._withparts(*parts)
