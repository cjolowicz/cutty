"""Unit tests for cutty.util.peek."""
from collections.abc import Iterable

from cutty.util.peek import peek


def test_peek_empty() -> None:
    """It returns None."""
    iterable: Iterable[int]
    first, iterable = peek([])
    assert first is None
    assert not list(iterable)


def test_peek_default() -> None:
    """It returns the default."""
    iterable: Iterable[int]
    first, iterable = peek([], default=42)
    assert first == 42
    assert not list(iterable)


def test_peek_one() -> None:
    """It returns the first item."""
    iterable: Iterable[int]
    first, iterable = peek([1])
    assert first == 1
    assert list(iterable) == [1]


def test_peek_many() -> None:
    """It returns the first item."""
    iterable: Iterable[int]
    first, iterable = peek([1, 2])
    assert first == 1
    assert list(iterable) == [1, 2]
