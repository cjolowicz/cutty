"""Unit tests for cutty.filesystems.adapters.git."""
from __future__ import annotations

from pathlib import Path

import pygit2
import pytest

from cutty.filesystems.adapters.git import GitFilesystem
from cutty.filesystems.domain.filesystem import Access
from cutty.filesystems.domain.purepath import PurePath
from cutty.util.git import Repository


class TreeBuilder:
    """A helper class forming a wrapper around pygit2.TreeBuilder."""

    def __init__(self, repository: Repository) -> None:
        """Initialize."""
        self.repository = repository
        self.builder = self.repository._repository.TreeBuilder()
        self.children: dict[str, TreeBuilder] = {}

    def _child(self, name: str) -> TreeBuilder:
        return self.children.setdefault(name, TreeBuilder(self.repository))

    def _descendant(self, path: PurePath) -> TreeBuilder:
        builder = self
        for name in path.parts:
            builder = builder._child(name)
        return builder

    def file(self, path: PurePath, text: str) -> None:
        """Create a regular file."""
        builder = self._descendant(path.parent)
        builder._blob(path.name, text, pygit2.GIT_FILEMODE_BLOB)

    def exec(self, path: PurePath, text: str) -> None:
        """Create an executable file."""
        builder = self._descendant(path.parent)
        builder._blob(path.name, text, pygit2.GIT_FILEMODE_BLOB_EXECUTABLE)

    def link(self, path: PurePath, target: str) -> None:
        """Create a symbolic link."""
        builder = self._descendant(path.parent)
        builder._blob(path.name, target, pygit2.GIT_FILEMODE_LINK)

    def _tree(self, name: str, builder: TreeBuilder) -> None:
        oid = builder.write()
        self.builder.insert(name, oid, pygit2.GIT_FILEMODE_TREE)

    def _blob(self, name: str, text: str, attr: int) -> None:
        oid = self.repository._repository.create_blob(text.encode())
        self.builder.insert(name, oid, attr)

    def write(self) -> pygit2.Oid:
        """Write the tree to the object database."""
        for name, child in self.children.items():
            self._tree(name, child)

        return self.builder.write()


@pytest.fixture
def filesystem(tmp_path: Path) -> GitFilesystem:
    """Fixture for a git filesystem."""
    repository = Repository.init(tmp_path / "repository")

    builder = TreeBuilder(repository)
    builder.file(PurePath("file"), "lorem ipsum dolor\n")
    builder.exec(PurePath("dir", "script.py"), "#!/usr/bin/env python\n")
    builder.link(PurePath("dir", "link"), "../file")
    builder.file(PurePath("dir", "subdir", ".keep"), "")
    builder.link(PurePath("sh"), "/bin/sh")

    author = committer = repository.default_signature
    repository._repository.create_commit(
        "HEAD",
        author,
        committer,
        "Initial",
        builder.write(),
        [],
    )

    return GitFilesystem(repository.path)


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
