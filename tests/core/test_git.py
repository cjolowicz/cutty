"""Tests for the git module."""
from pathlib import Path

import pytest

from ..utils import commit
from cutty.core import git


@pytest.fixture
def mirror(tmp_path: Path, repository: git.Repository) -> git.Repository:
    """Mirror repository in a temporary directory."""
    return git.Repository.clone(str(repository.path), tmp_path / "mirror", mirror=True)


def test_tags(repository: git.Repository) -> None:
    """It returns the tags."""
    commit(repository)
    repository.tag("v1.0.0")
    assert repository.tags() == ["v1.0.0"]


def test_worktree(
    tmp_path: Path, repository: git.Repository, mirror: git.Repository
) -> None:
    """It adds and removes a worktree."""
    (repository.path / "README").touch()
    repository.add("README")
    commit(repository)
    mirror.update_remote()
    path = tmp_path / "worktree"
    worktree = mirror.add_worktree(path, "HEAD", detach=True)
    assert (worktree.path / "README").is_file()
    mirror.remove_worktree(path)
    assert not (worktree.path / "README").exists()


def test_rev_parse(repository: git.Repository) -> None:
    """It returns the SHA1 hash."""
    commit(repository)
    assert repository.rev_parse("HEAD")


def test_clone_non_existing_directory() -> None:
    """It raises an error."""
    with pytest.raises(git.Error, match="does not exist"):
        git.Repository.clone("/no/such/directory")


def test_error_without_stderr(repository: git.Repository) -> None:
    """It reports the exit status."""
    with pytest.raises(git.Error, match="exit status"):
        repository.git("rev-parse", "--verify", "--quiet", "no-such-revision")


@pytest.mark.parametrize(
    "version,expected",
    [
        # fmt: off
        ("0.99",             git.Version(major=0, minor=99, patch=0)),
        ("0.99.9n",          git.Version(major=0, minor=99, patch=9)),
        ("1.0rc6",           git.Version(major=1, minor=0,  patch=0)),
        ("1.0.0",            git.Version(major=1, minor=0,  patch=0)),
        ("1.0.0b",           git.Version(major=1, minor=0,  patch=0)),
        ("1.8.5.6",          git.Version(major=1, minor=8,  patch=5)),
        ("1.9-rc2",          git.Version(major=1, minor=9,  patch=0)),
        ("2.4.12",           git.Version(major=2, minor=4,  patch=12)),
        ("2.29.2.windows.3", git.Version(major=2, minor=29, patch=2)),  # GitHub Actions
        ("2.30.0",           git.Version(major=2, minor=30, patch=0)),
        ("2.30.0-rc0",       git.Version(major=2, minor=30, patch=0)),
        ("2.30.0-rc2",       git.Version(major=2, minor=30, patch=0)),
        # fmt: on
    ],
)
def test_valid_version(version: str, expected: git.Version) -> None:
    """It produces the expected version."""
    assert expected == git.Version.parse(version)


@pytest.mark.parametrize(
    "version",
    [
        "",
        "0",
        "1",
        "a",
        "1a",
        "1.a",
        "1a.0.0",
        "lorem.1.0.0",
        "1:1.0.0",
    ],
)
def test_invalid_version(version: str) -> None:
    """It raises an exception."""
    with pytest.raises(ValueError):
        git.Version.parse(version)
