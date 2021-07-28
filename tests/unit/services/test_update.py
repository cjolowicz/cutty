"""Unit tests for cutty.services.update."""
from pathlib import Path

import pygit2
import pytest

from cutty.filestorage.adapters.observers.git import LATEST_BRANCH
from cutty.filestorage.adapters.observers.git import UPDATE_BRANCH
from cutty.services.update import abortupdate
from cutty.services.update import cherrypick
from cutty.services.update import continueupdate
from cutty.services.update import createworktree
from cutty.services.update import resetmerge
from cutty.services.update import skipupdate
from tests.util.files import chdir
from tests.util.git import commit
from tests.util.git import removefile
from tests.util.git import resolveconflicts
from tests.util.git import Side
from tests.util.git import updatefile
from tests.util.git import updatefiles


@pytest.fixture
def repositorypath(tmp_path: Path) -> Path:
    """Fixture for a repository."""
    repositorypath = tmp_path / "repository"
    pygit2.init_repository(repositorypath)
    return repositorypath


@pytest.fixture
def repository(repositorypath: Path) -> pygit2.Repository:
    """Fixture for a repository."""
    return pygit2.Repository(repositorypath)


def createbranch(repository: pygit2.Repository, name: str) -> pygit2.Branch:
    """Create a branch at HEAD."""
    return repository.branches.create(name, repository.head.peel())


def test_createworktree_creates_worktree(
    repository: pygit2.Repository, repositorypath: Path
) -> None:
    """It creates a worktree."""
    commit(repositorypath)
    createbranch(repository, "branch")

    with createworktree(repositorypath, "branch") as worktree:
        assert (worktree / ".git").is_file()


def test_createworktree_removes_worktree_on_exit(
    repository: pygit2.Repository, repositorypath: Path
) -> None:
    """It removes the worktree on exit."""
    commit(repositorypath)
    createbranch(repository, "branch")

    with createworktree(repositorypath, "branch") as worktree:
        pass

    assert not worktree.is_dir()


def test_createworktree_does_checkout(
    repository: pygit2.Repository, repositorypath: Path
) -> None:
    """It checks out a working tree."""
    updatefile(repositorypath / "README")
    createbranch(repository, "branch")

    with createworktree(repositorypath, "branch") as worktree:
        assert (worktree / "README").is_file()


def test_createworktree_no_checkout(
    repository: pygit2.Repository, repositorypath: Path
) -> None:
    """It creates a worktree without checking out the files."""
    updatefile(repositorypath / "README")
    createbranch(repository, "branch")

    with createworktree(repositorypath, "branch", checkout=False) as worktree:
        assert not (worktree / "README").is_file()


def test_cherrypick_adds_file(
    repository: pygit2.Repository, repositorypath: Path
) -> None:
    """It cherry-picks the commit onto the current branch."""
    commit(repositorypath)

    main = repository.head
    branch = createbranch(repository, "branch")
    path = repositorypath / "README"

    repository.checkout(branch)
    updatefile(path)

    repository.checkout(main)
    assert not path.is_file()

    cherrypick(repositorypath, branch.name)
    assert path.is_file()


def test_cherrypick_conflict_edit(
    repository: pygit2.Repository, repositorypath: Path
) -> None:
    """It raises an exception when both sides modified the file."""
    commit(repositorypath)

    main = repository.head
    branch = createbranch(repository, "branch")
    path = repositorypath / "README"

    repository.checkout(branch)
    updatefile(path, "a")

    repository.checkout(main)
    updatefile(path, "b")

    with pytest.raises(Exception, match=path.name):
        cherrypick(repositorypath, branch.name)


def test_cherrypick_conflict_deletion(
    repository: pygit2.Repository, repositorypath: Path
) -> None:
    """It raises an exception when one side modified and the other deleted the file."""
    path = repositorypath / "README"
    updatefile(path, "a")

    main = repository.head
    branch = createbranch(repository, "branch")

    repository.checkout(branch)
    updatefile(path, "b")

    repository.checkout(main)
    removefile(path)

    with pytest.raises(Exception, match=path.name):
        cherrypick(repositorypath, branch.name)


def createconflict(repositorypath: Path, path: Path, text1: str, text2: str) -> None:
    """Create an update conflict."""
    repository = pygit2.Repository(repositorypath)
    commit(repositorypath)

    main = repository.head
    update = createbranch(repository, UPDATE_BRANCH)
    createbranch(repository, LATEST_BRANCH)

    repository.checkout(update)
    updatefile(path, text1)

    repository.checkout(main)
    updatefile(path, text2)

    with pytest.raises(Exception, match=path.name):
        cherrypick(repositorypath, update.name)


def test_continueupdate_commits_changes(
    repository: pygit2.Repository, repositorypath: Path
) -> None:
    """It commits the changes."""
    path = repositorypath / "README"

    createconflict(repositorypath, path, "a", "b")
    resolveconflicts(repositorypath, path, Side.THEIRS)

    with chdir(repositorypath):
        continueupdate()

    blob = repository.head.peel().tree / path.name
    assert blob.data == b"a"


def test_continueupdate_fastforwards_latest(
    repository: pygit2.Repository, repositorypath: Path
) -> None:
    """It updates the latest branch to the tip of the update branch."""
    path = repositorypath / "README"

    createconflict(repositorypath, path, "a", "b")
    resolveconflicts(repositorypath, path, Side.THEIRS)

    with chdir(repositorypath):
        continueupdate()

    branches = repository.branches
    assert branches[LATEST_BRANCH].peel() == branches[UPDATE_BRANCH].peel()


def test_resetmerge_restores_files_with_conflicts(repositorypath: Path) -> None:
    """It restores the conflicting files in the working tree to our version."""
    path = repositorypath / "README"

    createconflict(repositorypath, path, "a", "b")
    resetmerge(repositorypath, parent=LATEST_BRANCH, cherry=UPDATE_BRANCH)

    assert path.read_text() == "b"


def test_resetmerge_restores_files_without_conflict(
    repository: pygit2.Repository, repositorypath: Path
) -> None:
    """It restores non-conflicting files in the working tree to our version."""
    commit(repositorypath)

    main = repository.head
    update = createbranch(repository, UPDATE_BRANCH)
    createbranch(repository, LATEST_BRANCH)

    path1 = repositorypath / "README"
    path2 = repositorypath / "LICENSE"

    repository.checkout(update)
    updatefiles({path1: "a", path2: ""})

    repository.checkout(main)
    updatefile(path1, "b")

    with pytest.raises(Exception, match=path1.name):
        cherrypick(repositorypath, update.name)

    resetmerge(repositorypath, parent=LATEST_BRANCH, cherry=UPDATE_BRANCH)

    assert not path2.exists()


def test_resetmerge_keeps_unrelated_additions(
    repository: pygit2.Repository, repositorypath: Path
) -> None:
    """It keeps additions of files that did not change in the update."""
    commit(repositorypath)

    main = repository.head
    update = createbranch(repository, UPDATE_BRANCH)
    createbranch(repository, LATEST_BRANCH)

    path1 = repositorypath / "README"
    path2 = repositorypath / "LICENSE"

    repository.checkout(update)
    updatefile(path1, "a")

    repository.checkout(main)
    updatefile(path1, "b")

    path2.touch()

    with pytest.raises(Exception, match=path1.name):
        cherrypick(repositorypath, update.name)

    resetmerge(repositorypath, parent=LATEST_BRANCH, cherry=UPDATE_BRANCH)

    assert path2.exists()


def test_resetmerge_keeps_unrelated_changes(
    repository: pygit2.Repository, repositorypath: Path
) -> None:
    """It keeps modifications to files that did not change in the update."""
    commit(repositorypath)

    main = repository.head
    update = createbranch(repository, UPDATE_BRANCH)
    createbranch(repository, LATEST_BRANCH)

    path1 = repositorypath / "README"
    path2 = repositorypath / "LICENSE"

    repository.checkout(update)
    updatefile(path1, "a")

    repository.checkout(main)
    updatefile(path1, "b")
    updatefile(path2)

    path2.write_text("c")

    with pytest.raises(Exception, match=path1.name):
        cherrypick(repositorypath, update.name)

    resetmerge(repositorypath, parent=LATEST_BRANCH, cherry=UPDATE_BRANCH)

    assert path2.read_text() == "c"


def test_resetmerge_keeps_unrelated_deletions(
    repository: pygit2.Repository, repositorypath: Path
) -> None:
    """It keeps deletions of files that did not change in the update."""
    commit(repositorypath)

    main = repository.head
    update = createbranch(repository, UPDATE_BRANCH)
    createbranch(repository, LATEST_BRANCH)

    path1 = repositorypath / "README"
    path2 = repositorypath / "LICENSE"

    repository.checkout(update)
    updatefile(path1, "a")

    repository.checkout(main)
    updatefile(path2)
    updatefile(path1, "b")

    path2.unlink()

    with pytest.raises(Exception, match=path1.name):
        cherrypick(repositorypath, update.name)

    resetmerge(repositorypath, parent=LATEST_BRANCH, cherry=UPDATE_BRANCH)

    assert not path2.exists()


def test_resetmerge_resets_index(
    repository: pygit2.Repository, repositorypath: Path
) -> None:
    """It resets the index to HEAD, removing conflicts."""
    createconflict(repositorypath, repositorypath / "README", "a", "b")

    resetmerge(repositorypath, parent=LATEST_BRANCH, cherry=UPDATE_BRANCH)

    assert repository.index.write_tree() == repository.head.peel().tree.id


def test_skipupdate_fastforwards_latest(
    repository: pygit2.Repository, repositorypath: Path
) -> None:
    """It fast-forwards the latest branch to the tip of the update branch."""
    createconflict(repositorypath, repositorypath / "README", "a", "b")

    updatehead = repository.branches[UPDATE_BRANCH].peel()

    with chdir(repositorypath):
        skipupdate()

    assert repository.branches[LATEST_BRANCH].peel() == updatehead


def test_abortupdate_rewinds_update_branch(
    repository: pygit2.Repository, repositorypath: Path
) -> None:
    """It resets the update branch to the tip of the latest branch."""
    createconflict(repositorypath, repositorypath / "README", "a", "b")

    branches = repository.branches
    latesthead = branches[LATEST_BRANCH].peel()

    with chdir(repositorypath):
        abortupdate()

    assert (
        branches[LATEST_BRANCH].peel() == latesthead == branches[UPDATE_BRANCH].peel()
    )
