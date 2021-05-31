"""Unit tests for cutty.filesystems.adapters.git."""
from pathlib import Path

import pygit2
import pytest

from cutty.filesystems.adapters.git import GitFilesystem
from cutty.filesystems.domain.filesystem import Access
from cutty.filesystems.domain.purepath import PurePath


@pytest.fixture
def filesystem(tmp_path: Path) -> GitFilesystem:
    """Fixture for a git filesystem."""
    (tmp_path / "file").write_text("lorem ipsum dolor\n")
    (tmp_path / "dir").mkdir()
    (tmp_path / "dir" / "script.py").write_text("#!/usr/bin/env python\n")
    (tmp_path / "dir" / "script.py").chmod(0o755)
    (tmp_path / "dir" / "link").symlink_to("../file")
    (tmp_path / "dir" / "subdir").mkdir()
    (tmp_path / "dir" / "subdir" / ".keep").touch()
    (tmp_path / "sh").symlink_to("/bin/sh")

    signature = pygit2.Signature("you", "you@example.com")
    repository = pygit2.init_repository(tmp_path)
    repository.index.add("file")
    repository.index.add("dir/script.py")
    repository.index.add("dir/link")
    repository.index.add("dir/subdir/.keep")
    repository.index.add("sh")
    repository.create_commit(
        "HEAD",
        signature,
        signature,
        "Initial",
        repository.index.write_tree(),
        [],
    )

    return GitFilesystem(tmp_path)


@pytest.mark.parametrize(
    "path",
    [
        PurePath("file"),
        PurePath("dir", "script.py"),
        PurePath("dir", "link"),
        PurePath(".", "file"),
        PurePath("..", "file"),
        PurePath("dir", ".", "script.py"),
    ],
    ids=str,
)
def test_is_file_true(filesystem: GitFilesystem, path: PurePath) -> None:
    """It returns True."""
    assert filesystem.is_file(path)


@pytest.mark.parametrize(
    "path",
    [
        PurePath("dir"),
        PurePath("dir", "subdir"),
        PurePath("."),
        PurePath(".."),
        PurePath("sh"),
    ],
    ids=str,
)
def test_is_file_false(filesystem: GitFilesystem, path: PurePath) -> None:
    """It returns False."""
    assert not filesystem.is_file(path)


@pytest.mark.parametrize(
    "path",
    [
        PurePath(),
        PurePath("dir"),
        PurePath("dir", "subdir"),
        PurePath("."),
        PurePath(".."),
        PurePath("..", ".."),
        PurePath("dir", "."),
        PurePath("dir", ".."),
        PurePath(".", "dir"),
        PurePath("..", "dir"),
        PurePath("dir", ".", "subdir"),
        PurePath("dir", "subdir", ".."),
    ],
    ids=str,
)
def test_is_dir_true(filesystem: GitFilesystem, path: PurePath) -> None:
    """It returns True."""
    assert filesystem.is_dir(path)


@pytest.mark.parametrize(
    "path",
    [
        PurePath("file"),
    ],
    ids=str,
)
def test_is_dir_false(filesystem: GitFilesystem, path: PurePath) -> None:
    """It returns False."""
    assert not filesystem.is_dir(path)


def test_iterdir(filesystem: GitFilesystem) -> None:
    """It returns the directory entries."""
    [entry] = filesystem.iterdir(PurePath("dir", "subdir"))
    assert entry == ".keep"


def test_read_text_symlink(filesystem: GitFilesystem) -> None:
    """It returns the contents of the target."""
    assert filesystem.read_text(PurePath("dir", "link")) == "lorem ipsum dolor\n"


@pytest.mark.parametrize(
    "path",
    [
        PurePath("dir", "script.py"),
        PurePath("dir", ".", "script.py"),
    ],
    ids=str,
)
def test_access_executable(filesystem: GitFilesystem, path: PurePath) -> None:
    """It returns True."""
    assert filesystem.access(path, Access.EXECUTE)
