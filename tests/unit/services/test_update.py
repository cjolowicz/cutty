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


def test_createworktree_creates_worktree(
    repository: pygit2.Repository, repositorypath: Path
) -> None:
    """It creates a worktree."""
    commit(repositorypath)
    repository.branches.create("branch", repository.head.peel())

    with createworktree(repositorypath, "branch") as worktree:
        assert (worktree / ".git").is_file()


def test_createworktree_removes_worktree_on_exit(
    repository: pygit2.Repository, repositorypath: Path
) -> None:
    """It removes the worktree on exit."""
    commit(repositorypath)
    repository.branches.create("branch", repository.head.peel())

    with createworktree(repositorypath, "branch") as worktree:
        pass

    assert not worktree.is_dir()


def test_createworktree_does_checkout(
    repository: pygit2.Repository, repositorypath: Path
) -> None:
    """It checks out a working tree."""
    updatefile(repositorypath / "README")
    repository.branches.create("branch", repository.head.peel())

    with createworktree(repositorypath, "branch") as worktree:
        assert (worktree / "README").is_file()


def test_createworktree_no_checkout(
    repository: pygit2.Repository, repositorypath: Path
) -> None:
    """It creates a worktree without checking out the files."""
    updatefile(repositorypath / "README")
    repository.branches.create("branch", repository.head.peel())

    with createworktree(repositorypath, "branch", checkout=False) as worktree:
        assert not (worktree / "README").is_file()


def test_cherrypick_adds_file(
    repository: pygit2.Repository, repositorypath: Path
) -> None:
    """It cherry-picks the commit onto the current branch."""
    commit(repositorypath)

    main = repository.references[repository.references["HEAD"].target]
    branch = repository.branches.create("branch", repository.head.peel())
    path = repositorypath / "README"

    repository.checkout(branch)
    updatefile(path)

    repository.checkout(main)
    assert not path.is_file()

    cherrypick(repositorypath, "refs/heads/branch")
    assert path.is_file()


def test_cherrypick_conflict(
    repository: pygit2.Repository, repositorypath: Path
) -> None:
    """It raises an exception on merge conflicts."""
    commit(repositorypath)

    main = repository.references[repository.references["HEAD"].target]
    branch = repository.branches.create("branch", repository.head.peel())
    path = repositorypath / "README"

    repository.checkout(branch)
    updatefile(path, "This is the version on the other branch.")

    repository.checkout(main)
    updatefile(path, "This is the version on the main branch.")

    with pytest.raises(Exception, match=path.name):
        cherrypick(repositorypath, branch.name)


def test_cherrypick_conflict_deletion(
    repository: pygit2.Repository, repositorypath: Path
) -> None:
    """It does not crash when the merge conflict involves file deletions."""
    path = repositorypath / "README"
    updatefile(path, "This is the initial version.")

    main = repository.references["HEAD"].target
    branch = repository.branches.create("mybranch", repository.head.peel())

    path.unlink()
    commit(repositorypath, message="Remove README")

    repository.checkout(branch)
    path.write_text("This is the version on the other branch.")
    commit(repositorypath, message="Update README")

    repository.checkout(repository.references[main])

    with pytest.raises(Exception, match=path.name):
        cherrypick(repositorypath, branch.name)


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


def createconflict(repositorypath: Path, path: Path, text1: str, text2: str) -> None:
    """Fixture for an update conflict."""
    repository = pygit2.Repository(repositorypath)
    commit(repositorypath, message="Initial")

    main = repository.references[repository.references["HEAD"].target]
    update = repository.branches.create(UPDATE_BRANCH, repository.head.peel())
    repository.branches.create(LATEST_BRANCH, repository.head.peel())

    repository.checkout(update)
    updatefile(path, text1)

    repository.checkout(main)
    updatefile(path, text2)

    with pytest.raises(Exception, match=path.name):
        cherrypick(repositorypath, update.name)


def test_resetmerge_restores_files_with_conflicts(repositorypath: Path) -> None:
    """It restores the conflicting files in the working tree to our version."""
    path = repositorypath / "README"
    createconflict(
        repositorypath,
        path,
        "This is the version on the update branch.",
        "This is the version on the main branch.",
    )

    resetmerge(repositorypath, parent=LATEST_BRANCH, cherry=UPDATE_BRANCH)

    assert path.read_text() == "This is the version on the main branch."


def test_resetmerge_restores_files_without_conflict(repositorypath: Path) -> None:
    """It restores non-conflicting files in the working tree to our version."""
    repository = pygit2.Repository(repositorypath)
    commit(repositorypath, message="Initial")

    main = repository.references[repository.references["HEAD"].target]
    update = repository.branches.create(UPDATE_BRANCH, repository.head.peel())
    repository.branches.create(LATEST_BRANCH, repository.head.peel())

    readme = repositorypath / "README"
    license = repositorypath / "LICENSE"

    repository.checkout(update)
    updatefiles({license: "", readme: "This is the version on the update branch."})

    repository.checkout(main)
    updatefile(readme, "This is the version on the main branch.")

    with pytest.raises(Exception, match=readme.name):
        cherrypick(repositorypath, update.name)

    resetmerge(repositorypath, parent=LATEST_BRANCH, cherry=UPDATE_BRANCH)

    assert not license.exists()


def test_resetmerge_keeps_unrelated_additions(repositorypath: Path) -> None:
    """It keeps additions of files that did not change in the update."""
    repository = pygit2.Repository(repositorypath)
    commit(repositorypath, message="Initial")

    main = repository.references[repository.references["HEAD"].target]
    update = repository.branches.create(UPDATE_BRANCH, repository.head.peel())
    repository.branches.create(LATEST_BRANCH, repository.head.peel())

    readme = repositorypath / "README"
    license = repositorypath / "LICENSE"

    repository.checkout(update)
    updatefile(readme, "This is the version on the update branch.")

    repository.checkout(main)
    updatefile(readme, "This is the version on the main branch.")

    license.touch()

    with pytest.raises(Exception, match=readme.name):
        cherrypick(repositorypath, update.name)

    resetmerge(repositorypath, parent=LATEST_BRANCH, cherry=UPDATE_BRANCH)

    assert license.exists()


def test_resetmerge_keeps_unrelated_changes(repositorypath: Path) -> None:
    """It keeps modifications to files that did not change in the update."""
    repository = pygit2.Repository(repositorypath)
    commit(repositorypath, message="Initial")

    main = repository.references[repository.references["HEAD"].target]
    update = repository.branches.create(UPDATE_BRANCH, repository.head.peel())
    repository.branches.create(LATEST_BRANCH, repository.head.peel())

    readme = repositorypath / "README"
    license = repositorypath / "LICENSE"

    repository.checkout(update)
    updatefile(readme, "This is the version on the update branch.")

    repository.checkout(main)
    updatefile(license)
    updatefile(readme, "This is the version on the main branch.")

    license.write_text("This is an unstaged change.")

    with pytest.raises(Exception, match=readme.name):
        cherrypick(repositorypath, update.name)

    resetmerge(repositorypath, parent=LATEST_BRANCH, cherry=UPDATE_BRANCH)

    assert license.read_text() == "This is an unstaged change."


def test_resetmerge_keeps_unrelated_deletions(repositorypath: Path) -> None:
    """It keeps deletions of files that did not change in the update."""
    repository = pygit2.Repository(repositorypath)
    commit(repositorypath, message="Initial")

    main = repository.references[repository.references["HEAD"].target]
    update = repository.branches.create(UPDATE_BRANCH, repository.head.peel())
    repository.branches.create(LATEST_BRANCH, repository.head.peel())

    readme = repositorypath / "README"
    license = repositorypath / "LICENSE"

    repository.checkout(update)
    updatefile(readme, "This is the version on the update branch.")

    repository.checkout(main)
    updatefile(license)
    updatefile(readme, "This is the version on the main branch.")

    license.unlink()

    with pytest.raises(Exception, match=readme.name):
        cherrypick(repositorypath, update.name)

    resetmerge(repositorypath, parent=LATEST_BRANCH, cherry=UPDATE_BRANCH)

    assert not license.exists()


def test_resetmerge_resets_index(repositorypath: Path) -> None:
    """It resets the index to HEAD, removing conflicts."""
    createconflict(
        repositorypath,
        repositorypath / "README",
        "This is the version on the update branch.",
        "This is the version on the main branch.",
    )

    resetmerge(repositorypath, parent=LATEST_BRANCH, cherry=UPDATE_BRANCH)

    repository = pygit2.Repository(repositorypath)
    assert repository.index.write_tree() == repository.head.peel().tree.id


def test_skipupdate_fastforwards_latest(repositorypath: Path) -> None:
    """It fast-forwards the latest branch to the tip of the update branch."""
    createconflict(
        repositorypath,
        repositorypath / "README",
        "This is the version on the update branch.",
        "This is the version on the main branch.",
    )

    branches = pygit2.Repository(repositorypath).branches
    updatehead = branches[UPDATE_BRANCH].peel()

    with chdir(repositorypath):
        skipupdate()

    assert branches[LATEST_BRANCH].peel() == updatehead


def test_abortupdate_rewinds_update_branch(repositorypath: Path) -> None:
    """It resets the update branch to the tip of the latest branch."""
    createconflict(
        repositorypath,
        repositorypath / "README",
        "This is the version on the update branch.",
        "This is the version on the main branch.",
    )

    branches = pygit2.Repository(repositorypath).branches
    latesthead = branches[LATEST_BRANCH].peel()

    with chdir(repositorypath):
        abortupdate()

    assert (
        branches[LATEST_BRANCH].peel() == latesthead == branches[UPDATE_BRANCH].peel()
    )
