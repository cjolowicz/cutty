"""Unit tests for cutty.filesystem.domain.purepath."""
import pytest

from cutty.filesystem.domain.purepath import PurePath


@pytest.mark.parametrize(
    "parts",
    [
        [],
        ["README.md"],
        ["example", "README.md"],
        [""],
        ["example", ""],
        ["", "example"],
        ["example", "", "README.md"],
        ["/", "boot", "vmlinuz"],
        ["\\", "system32", "hal.dll"],
        ["..", "README.md"],
        ["example", ".", "README.md"],
    ],
)
def test_valid(parts: list[str]) -> None:
    """It returns a PurePath instance."""
    assert PurePath(*parts)


def test_div() -> None:
    """It returns a path with the part appended."""
    assert PurePath("etc") / "passwd" == PurePath("etc", "passwd")


@pytest.mark.parametrize(
    "path,expected",
    [
        (PurePath(), ""),
        (PurePath("README.md"), "README.md"),
        (PurePath("example", "README.md"), "README.md"),
    ],
)
def test_name(path: PurePath, expected: str) -> None:
    """It returns the final component, if any."""
    assert path.name == expected


@pytest.mark.parametrize(
    "path,expected",
    [
        (PurePath(), ""),
        (PurePath("README"), "README"),
        (PurePath("README.md"), "README"),
        (PurePath("example", "README.md"), "README"),
        (PurePath("archive.tar.gz"), "archive.tar"),
        (PurePath(".profile"), ".profile"),
    ],
)
def test_stem(path: PurePath, expected: str) -> None:
    """It returns the final component, minus its last suffix."""
    assert path.stem == expected
