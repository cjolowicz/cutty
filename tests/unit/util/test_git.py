"""Unit tests for cutty.util.git."""
from collections.abc import Iterator
from pathlib import Path

import pygit2
import pytest

from cutty.util.git import cherrypick
from cutty.util.git import createbranch as createbranch_
from cutty.util.git import createworktree
from cutty.util.git import resetmerge
from tests.util.git import removefile
from tests.util.git import updatefile
from tests.util.git import updatefiles


pytest_plugins = ["tests.fixtures.git"]


def test_createbranch_target_default(repository: pygit2.Repository) -> None:
    """It creates the branch at HEAD by default."""
    createbranch_(repository, "branch")

    assert repository.branches["branch"].peel() == repository.head.peel()


def createbranch(repository: pygit2.Repository, name: str) -> pygit2.Branch:
    """Create a branch at HEAD."""
    return repository.branches.create(name, repository.head.peel())


def createbranches(
    repository: pygit2.Repository, *names: str
) -> tuple[pygit2.Branch, ...]:
    """Create a branch at HEAD."""
    return tuple(createbranch(repository, name) for name in names)


def createconflict(repositorypath: Path, path: Path, *, ours: str, theirs: str) -> None:
    """Create an update conflict."""
    repository = pygit2.Repository(repositorypath)
    main = repository.head
    update, _ = createbranches(repository, "update", "latest")

    repository.checkout(update)
    updatefile(path, theirs)

    repository.checkout(main)
    updatefile(path, ours)

    with pytest.raises(Exception, match=path.name):
        cherrypick(repository, update.name, message="")


def test_createworktree_creates_worktree(repository: pygit2.Repository) -> None:
    """It creates a worktree."""
    createbranch(repository, "branch")

    with createworktree(repository, "branch") as worktree:
        assert (worktree / ".git").is_file()


def test_createworktree_removes_worktree_on_exit(repository: pygit2.Repository) -> None:
    """It removes the worktree on exit."""
    createbranch(repository, "branch")

    with createworktree(repository, "branch") as worktree:
        pass

    assert not worktree.is_dir()


def test_createworktree_does_checkout(
    repository: pygit2.Repository, path: Path
) -> None:
    """It checks out a working tree."""
    updatefile(path)
    createbranch(repository, "branch")

    with createworktree(repository, "branch") as worktree:
        assert (worktree / path.name).is_file()


def test_createworktree_no_checkout(repository: pygit2.Repository, path: Path) -> None:
    """It creates a worktree without checking out the files."""
    updatefile(path)
    createbranch(repository, "branch")

    with createworktree(repository, "branch", checkout=False) as worktree:
        assert not (worktree / path.name).is_file()


def test_cherrypick_adds_file(repository: pygit2.Repository, path: Path) -> None:
    """It cherry-picks the commit onto the current branch."""
    main = repository.head
    branch = createbranch(repository, "branch")

    repository.checkout(branch)
    updatefile(path)

    repository.checkout(main)
    assert not path.is_file()

    cherrypick(repository, branch.name, message="")
    assert path.is_file()


def test_cherrypick_conflict_edit(repository: pygit2.Repository, path: Path) -> None:
    """It raises an exception when both sides modified the file."""
    main = repository.head
    branch = createbranch(repository, "branch")

    repository.checkout(branch)
    updatefile(path, "a")

    repository.checkout(main)
    updatefile(path, "b")

    with pytest.raises(Exception, match=path.name):
        cherrypick(repository, branch.name, message="")


def test_cherrypick_conflict_deletion(
    repository: pygit2.Repository, path: Path
) -> None:
    """It raises an exception when one side modified and the other deleted the file."""
    updatefile(path, "a")

    main = repository.head
    branch = createbranch(repository, "branch")

    repository.checkout(branch)
    updatefile(path, "b")

    repository.checkout(main)
    removefile(path)

    with pytest.raises(Exception, match=path.name):
        cherrypick(repository, branch.name, message="")


def test_resetmerge_restores_files_with_conflicts(
    repository: pygit2.Repository, repositorypath: Path, path: Path
) -> None:
    """It restores the conflicting files in the working tree to our version."""
    createconflict(repositorypath, path, ours="a", theirs="b")
    resetmerge(repository, parent="latest", cherry="update")

    assert path.read_text() == "a"


def test_resetmerge_removes_added_files(
    repository: pygit2.Repository, paths: Iterator[Path]
) -> None:
    """It removes files added by the cherry-picked commit."""
    main = repository.head
    update, _ = createbranches(repository, "update", "latest")
    path1, path2 = next(paths), next(paths)

    repository.checkout(update)
    updatefiles({path1: "a", path2: ""})

    repository.checkout(main)
    updatefile(path1, "b")

    with pytest.raises(Exception, match=path1.name):
        cherrypick(repository, update.name, message="")

    resetmerge(repository, parent="latest", cherry="update")

    assert not path2.exists()


def test_resetmerge_keeps_unrelated_additions(
    repository: pygit2.Repository, paths: Iterator[Path]
) -> None:
    """It keeps additions of files that did not change in the update."""
    main = repository.head
    update, _ = createbranches(repository, "update", "latest")
    path1, path2 = next(paths), next(paths)

    repository.checkout(update)
    updatefile(path1, "a")

    repository.checkout(main)
    updatefile(path1, "b")

    path2.touch()

    with pytest.raises(Exception, match=path1.name):
        cherrypick(repository, update.name, message="")

    resetmerge(repository, parent="latest", cherry="update")

    assert path2.exists()


def test_resetmerge_keeps_unrelated_changes(
    repository: pygit2.Repository, paths: Iterator[Path]
) -> None:
    """It keeps modifications to files that did not change in the update."""
    main = repository.head
    update, _ = createbranches(repository, "update", "latest")
    path1, path2 = next(paths), next(paths)

    repository.checkout(update)
    updatefile(path1, "a")

    repository.checkout(main)
    updatefile(path1, "b")
    updatefile(path2)

    path2.write_text("c")

    with pytest.raises(Exception, match=path1.name):
        cherrypick(repository, update.name, message="")

    resetmerge(repository, parent="latest", cherry="update")

    assert path2.read_text() == "c"


def test_resetmerge_keeps_unrelated_deletions(
    repository: pygit2.Repository, paths: Iterator[Path]
) -> None:
    """It keeps deletions of files that did not change in the update."""
    main = repository.head
    update, _ = createbranches(repository, "update", "latest")
    path1, path2 = next(paths), next(paths)

    repository.checkout(update)
    updatefile(path1, "a")

    repository.checkout(main)
    updatefile(path1, "b")
    updatefile(path2)

    path2.unlink()

    with pytest.raises(Exception, match=path1.name):
        cherrypick(repository, update.name, message="")

    resetmerge(repository, parent="latest", cherry="update")

    assert not path2.exists()


def test_resetmerge_resets_index(
    repository: pygit2.Repository, repositorypath: Path, path: Path
) -> None:
    """It resets the index to HEAD, removing conflicts."""
    createconflict(repositorypath, path, ours="a", theirs="b")

    resetmerge(repository, parent="latest", cherry="update")

    assert repository.index.write_tree() == repository.head.peel().tree.id
