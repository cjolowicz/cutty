"""Unit tests for cutty.filesystems.domain.purepath."""
import pytest

from cutty.filesystems.domain.purepath import PurePath


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


def test_parents_getitem_slice() -> None:
    """It returns the expected slice of parents."""
    path = PurePath("usr", "share", "doc", "python3", "README.rst")
    assert path.parents[0] == path.parent
    assert path.parents[1] == path.parent.parent
    assert path.parents[:2] == (path.parent, path.parent.parent)
    assert path.parents[-2] == PurePath("usr")
    assert path.parents[-1] == PurePath()
    assert path.parents[-2:] == (PurePath("usr"), PurePath())
    with pytest.raises(IndexError):
        path.parents[len(path.parts)]
