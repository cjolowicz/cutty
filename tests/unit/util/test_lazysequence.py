"""Unit tests for cutty.util.lazysequence."""
import pytest

from cutty.util.lazysequence import LazySequence


def test_init() -> None:
    """It is created from an iterable."""
    LazySequence([])


def test_len() -> None:
    """It returns the number of items."""
    assert 0 == len(LazySequence([]))


def test_getitem() -> None:
    """It returns the item at the given position."""
    assert 1 == LazySequence([1])[0]


def test_getslice() -> None:
    """It returns the items at the given positions."""
    [item] = LazySequence([1, 2])[1:]
    assert 2 == item


def test_outofrange() -> None:
    """It raises IndexError."""
    with pytest.raises(IndexError):
        LazySequence([])[0]


def test_bool() -> None:
    """It is False for an empty sequence."""
    assert not LazySequence([])
