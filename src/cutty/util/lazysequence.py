"""Lazy sequences."""
from collections.abc import Iterable
from collections.abc import Iterator
from collections.abc import Sequence
from typing import overload
from typing import TypeVar
from typing import Union

_T_co = TypeVar("_T_co", covariant=True)


class LazySequence(Sequence[_T_co]):
    """Lazy sequence."""

    def __init__(self, iterable: Iterable[_T_co]) -> None:
        """Initialize."""
        self._iter = iter(iterable)
        self._cache: list[_T_co] = []

    def __iter__(self) -> Iterator[_T_co]:
        """Iterate over the items in the sequence."""
        for item in self._cache:
            yield item

        for item in self._iter:
            self._cache.append(item)
            yield item

    def __len__(self) -> int:
        """Return the length of the sequence."""
        return sum(1 for _ in self)

    @overload
    def __getitem__(self, i: int) -> _T_co:
        """Return the item at the given index."""  # noqa: D418

    @overload
    def __getitem__(self, s: slice) -> Sequence[_T_co]:
        """Return a slice of the sequence."""  # noqa: D418

    def __getitem__(self, index: Union[int, slice]) -> Union[_T_co, Sequence[_T_co]]:
        """Return the item at the given index."""
        if isinstance(index, slice):
            return LazySequence(
                self[position] for position in range(*index.indices(len(self)))
            )

        for position, item in enumerate(self):
            if index == position:
                return item

        raise IndexError("LazySequence index out of range")
