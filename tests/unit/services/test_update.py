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


@pytest.fixture
def repositorypath(tmp_path: Path) -> Path:
    """Fixture for a repository."""
    repositorypath = tmp_path / "repository"
    pygit2.init_repository(repositorypath)
    return repositorypath


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
