"""Unit tests for cutty.domain.paths."""
import pytest

from cutty.domain.paths import EmptyPathComponent
from cutty.domain.paths import InvalidPathComponent
from cutty.domain.paths import Path


@pytest.mark.parametrize(
    "parts",
    [
        [""],
        ["example", ""],
        ["", "example"],
        ["example", "", "README.md"],
    ],
)
def test_fromparts_empty(parts: list[str]) -> None:
    """It raises an exception."""
    with pytest.raises(EmptyPathComponent):
        Path.fromparts(parts)


@pytest.mark.parametrize(
    "parts",
    [
        ["/", "boot", "vmlinuz"],
        ["\\", "system32", "hal.dll"],
        ["..", "README.md"],
        ["example", ".", "README.md"],
    ],
)
def test_fromparts_invalid(parts: list[str]) -> None:
    """It raises an exception."""
    with pytest.raises(InvalidPathComponent):
        Path.fromparts(parts)


@pytest.mark.parametrize(
    "parts",
    [
        [],
        ["README.md"],
        ["example", "README.md"],
    ],
)
def test_fromparts_valid(parts: list[str]) -> None:
    """It returns a Path instance."""
    assert Path.fromparts(parts)
