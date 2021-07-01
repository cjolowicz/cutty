"""Lazy sequences."""
from collections import deque
from collections.abc import Iterable
from collections.abc import Iterator
from collections.abc import Sequence
from typing import overload
from typing import TypeVar
from typing import Union

_T_co = TypeVar("_T_co", covariant=True)


class LazySequence(Sequence[_T_co]):
    """A lazy sequence provides sequence operations on an iterable."""

    def __init__(self, iterable: Iterable[_T_co]) -> None:
        """Initialize."""
        self._iter = iter(iterable)
        self._cache: deque[_T_co] = deque()

    def _consume(self) -> Iterator[_T_co]:
        for item in self._iter:
            self._cache.append(item)
            yield item

    def __iter__(self) -> Iterator[_T_co]:
        """Iterate over the items in the sequence."""
        yield from self._cache
        yield from self._consume()

    def __bool__(self) -> bool:
        """Return True if there are any items in the sequence."""
        for _ in self:
            return True
        return False

    def __len__(self) -> int:
        """Return the number of items in the sequence."""
        return len(self._cache) + sum(1 for _ in self._consume())

    @overload
    def __getitem__(self, index: int) -> _T_co:
        """Return the item at the given index."""  # noqa: D418

    @overload
    def __getitem__(self, indices: slice) -> Sequence[_T_co]:
        """Return a slice of the sequence."""  # noqa: D418

    def __getitem__(self, index: Union[int, slice]) -> Union[_T_co, Sequence[_T_co]]:
        """Return the item at the given index."""
        if isinstance(index, slice):
            return LazySequence(
                self[position] for position in range(*index.indices(len(self)))
            )

        if index < 0:
            index += len(self)

        try:
            return self._cache[index]
        except IndexError:
            pass

        for position, item in enumerate(self._consume()):
            if index == position:
                return item

        raise IndexError("LazySequence index out of range")
