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

    def _blob(builder: pygit2.TreeBuilder, name: str, text: str, attr: int) -> None:
        builder.insert(name, repository.create_blob(text.encode()), attr)

    def _file(builder: pygit2.TreeBuilder, name: str, text: str) -> None:
        _blob(builder, name, text, pygit2.GIT_FILEMODE_BLOB)

    def _exec(builder: pygit2.TreeBuilder, name: str, text: str) -> None:
        _blob(builder, name, text, pygit2.GIT_FILEMODE_BLOB_EXECUTABLE)

    def _link(builder: pygit2.TreeBuilder, name: str, target: str) -> None:
        _blob(builder, name, target, pygit2.GIT_FILEMODE_LINK)

    def _tree(builder: pygit2.TreeBuilder, name: str, tree: pygit2.TreeBuilder) -> None:
        builder.insert(name, tree.write(), pygit2.GIT_FILEMODE_TREE)

    signature = pygit2.Signature("you", "you@example.com")
    repository = pygit2.init_repository(tmp_path)

    root = repository.TreeBuilder()
    root_dir = repository.TreeBuilder()
    root_dir_subdir = repository.TreeBuilder()

    _file(root, "file", "lorem ipsum dolor\n")
    _exec(root_dir, "script.py", "#!/usr/bin/env python\n")
    _link(root_dir, "link", "../file")
    _file(root_dir_subdir, ".keep", "")
    _tree(root_dir, "subdir", root_dir_subdir)
    _tree(root, "dir", root_dir)
    _link(root, "sh", "/bin/sh")

    repository.create_commit(
        "HEAD",
        signature,
        signature,
        "Initial",
        root.write(),
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
