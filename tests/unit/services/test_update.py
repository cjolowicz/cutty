"""Unit tests for cutty.services.update."""
from pathlib import Path

import pygit2
import pytest

from cutty.filestorage.adapters.observers.git import LATEST_BRANCH
from cutty.filestorage.adapters.observers.git import UPDATE_BRANCH
from cutty.services.update import cherrypick
from cutty.services.update import continueupdate
from cutty.services.update import createworktree
from tests.util.files import chdir
from tests.util.git import commit
from tests.util.git import resolveconflicts
from tests.util.git import Side


def test_createworktree(tmp_path: Path) -> None:
    """It returns a path to the worktree."""
    repositorypath = tmp_path / "repository"
    repository = pygit2.init_repository(repositorypath)
    (tmp_path / "repository" / "README").touch()
    commit(repositorypath, message="Initial")
    repository.branches.create("mybranch", repository.head.peel())

    with createworktree(repositorypath, "mybranch") as worktree:
        assert (worktree / ".git").is_file()
        assert (worktree / "README").is_file()

    assert not worktree.is_dir()


def test_createworktree_no_checkout(tmp_path: Path) -> None:
    """It creates a worktree without checking out the files."""
    repositorypath = tmp_path / "repository"
    repository = pygit2.init_repository(repositorypath)
    (tmp_path / "repository" / "README").touch()
    commit(repositorypath, message="Initial")
    repository.branches.create("mybranch", repository.head.peel())

    with createworktree(repositorypath, "mybranch", checkout=False) as worktree:
        assert (worktree / ".git").is_file()
        assert not (worktree / "README").is_file()


def test_cherrypick(tmp_path: Path) -> None:
    """It cherry-picks the commit onto the current branch."""
    repositorypath = tmp_path / "repository"
    repository = pygit2.init_repository(repositorypath)
    commit(repositorypath, message="Initial")

    currentbranch = repository.references["HEAD"].target
    otherbranch = "mybranch"

    (repositorypath / "README").touch()
    repository.branches.create(otherbranch, repository.head.peel())
    repository.set_head(f"refs/heads/{otherbranch}")
    commit(repositorypath, message="Add README")

    repository.checkout(currentbranch)
    assert not (repositorypath / "README").is_file()

    cherrypick(repositorypath, f"refs/heads/{otherbranch}")
    assert (repositorypath / "README").is_file()


def test_cherrypick_conflict(tmp_path: Path) -> None:
    """It raises an exception on merge conflicts."""
    repositorypath = tmp_path / "repository"
    repository = pygit2.init_repository(repositorypath)
    commit(repositorypath, message="Initial")

    mainbranch = repository.references[repository.references["HEAD"].target]
    otherbranch = repository.branches.create("mybranch", repository.head.peel())

    (repositorypath / "README").write_text("This is the version on the main branch.")
    commit(repositorypath, message="Add README")

    repository.checkout(otherbranch)
    (repositorypath / "README").write_text("This is the version on the other branch.")
    commit(repositorypath, message="Add README")

    repository.checkout(mainbranch)

    with pytest.raises(Exception, match="README"):
        cherrypick(repositorypath, otherbranch.name)


def test_cherrypick_conflict_deletion(tmp_path: Path) -> None:
    """It does not crash when the merge conflict involves file deletions."""
    repositorypath = tmp_path / "repository"
    repository = pygit2.init_repository(repositorypath)
    (repositorypath / "README").write_text("This is the initial version.")
    commit(repositorypath, message="Initial")

    mainbranch = repository.references["HEAD"].target
    otherbranch = repository.branches.create("mybranch", repository.head.peel())

    (repositorypath / "README").unlink()
    commit(repositorypath, message="Remove README")

    repository.checkout(otherbranch)
    (repositorypath / "README").write_text("This is the version on the other branch.")
    commit(repositorypath, message="Update README")

    repository.checkout(repository.references[mainbranch])

    with pytest.raises(Exception, match="README"):
        cherrypick(repositorypath, otherbranch.name)


def test_continueupdate(tmp_path: Path) -> None:
    """It commits the changes and updates the latest branch."""
    repositorypath = tmp_path / "repository"
    repository = pygit2.init_repository(repositorypath)
    commit(repositorypath, message="Initial")

    mainbranch = repository.references[repository.references["HEAD"].target]
    repository.branches.create(LATEST_BRANCH, repository.head.peel())
    updatebranch = repository.branches.create(UPDATE_BRANCH, repository.head.peel())

    (repositorypath / "README").write_text("This is the version on the main branch.")
    commit(repositorypath, message="Add README")

    repository.checkout(updatebranch)
    (repositorypath / "README").write_text("This is the version on the update branch.")
    commit(repositorypath, message="Add README")

    repository.checkout(mainbranch)

    with pytest.raises(Exception, match="README"):
        cherrypick(repositorypath, updatebranch.name)

    resolveconflicts(repositorypath, repositorypath / "README", Side.THEIRS)

    with chdir(repositorypath):
        continueupdate()

    blob = repository.head.peel().tree / "README"
    assert blob.data == b"This is the version on the update branch."
    assert (
        repository.branches[LATEST_BRANCH].peel()
        == repository.branches[UPDATE_BRANCH].peel()
    )
