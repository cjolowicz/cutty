"""Unit tests for cutty.util.reraise."""
import pytest

from cutty.util.reraise import reraise


def test_reraise_no_trigger() -> None:
    """It raises the given exception when another exception is caught."""
    with pytest.raises(RuntimeError):
        with reraise(RuntimeError("got exception")):
            raise ValueError("boom")


def test_reraise_no_trigger_base() -> None:
    """It does not reraise on base exceptions."""
    with pytest.raises(BaseException):
        with reraise(RuntimeError("got exception")):
            raise BaseException("boom")


def test_reraise_single_trigger() -> None:
    """It does not reraise on unrelated exceptions."""
    with pytest.raises(TypeError):
        with reraise(RuntimeError("got value error"), when=ValueError):
            raise TypeError("boom")


def test_reraise_multiple_triggers() -> None:
    """It does not reraise on unrelated exceptions."""
    with pytest.raises(TypeError):
        with reraise(RuntimeError("got value error"), when=(ValueError, KeyError)):
            raise TypeError("boom")
