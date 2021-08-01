"""Unit tests for cutty.util.git."""
from collections.abc import Iterator
from pathlib import Path

import pygit2
import pytest

from cutty.util.git import Repository
from tests.util.git import createbranches
from tests.util.git import removefile
from tests.util.git import updatefile
from tests.util.git import updatefiles


pytest_plugins = ["tests.fixtures.git"]


def test_branches_len_empty(tmp_path: Path) -> None:
    """It returns zero if there are no branches."""
    repository = Repository.init(tmp_path / "repository")
    assert not len(repository.branches)


def test_branches_len_nonzero(repository: Repository) -> None:
    """It returns the number of branches."""
    assert 1 == len(repository.branches)


def test_branches_bool_empty(tmp_path: Path) -> None:
    """It returns False if there are no branches."""
    repository = Repository.init(tmp_path / "repository")
    assert not repository.branches


def test_branches_bool_nonzero(repository: Repository) -> None:
    """It returns True if there are branches."""
    assert repository.branches


def test_branches_contains_false(repository: Repository) -> None:
    """It returns False if the branch does not exist."""
    assert "branch" not in repository.branches


def test_branches_contains_true(repository: Repository) -> None:
    """It returns True if the branch exists."""
    main = repository.references["HEAD"].target.removeprefix("refs/heads/")
    assert main in repository.branches


def test_branches_iter(repository: Repository) -> None:
    """It yields the name of each branch."""
    main = repository.references["HEAD"].target.removeprefix("refs/heads/")
    assert [main] == list(iter(repository.branches))


def test_branches_getitem_fail(repository: Repository) -> None:
    """It raises KeyError."""
    with pytest.raises(KeyError):
        repository.branches["branch"]


def test_branches_getitem_pass(repository: Repository) -> None:
    """It returns the commit at the head of the branch."""
    main = repository.references["HEAD"].target.removeprefix("refs/heads/")
    assert repository.head.peel() == repository.branches[main]


def test_branches_setitem_new(repository: Repository) -> None:
    """It creates a branch pointing to the given commit."""
    main = repository.references["HEAD"].target.removeprefix("refs/heads/")
    repository.branches["branch"] = repository.branches[main]
    assert repository.branches["branch"] == repository.branches[main]


def test_branches_setitem_existing(repository: Repository) -> None:
    """It resets the branch to the given commit."""
    main = repository.references["HEAD"].target.removeprefix("refs/heads/")
    branches = repository.branches
    branches["branch"] = branches[main]
    updatefile(repository.path / "file")
    branches["branch"] = branches[main]
    assert branches["branch"] == branches[main]


def test_branches_delitem_fail(repository: Repository) -> None:
    """It raises KeyError."""
    with pytest.raises(KeyError):
        del repository.branches["branch"]


def test_branches_delitem_pass(repository: Repository) -> None:
    """It removes the branch."""
    main = repository.references["HEAD"].target.removeprefix("refs/heads/")
    branches = repository.branches
    branches["branch"] = branches[main]
    del branches["branch"]
    assert "branch" not in branches


def test_branches_keys(repository: Repository) -> None:
    """It returns the branch names."""
    main = repository.references["HEAD"].target.removeprefix("refs/heads/")
    [branch] = repository.branches.keys()
    assert main == branch


def test_branches_pop(repository: Repository) -> None:
    """It removes the branch and returns the commit at its head."""
    main = repository.references["HEAD"].target.removeprefix("refs/heads/")
    branches = repository.branches
    branches["branch"] = branches[main]
    commit = branches.pop("branch")
    assert branches[main] == commit


def test_branches_branch_fail(repository: Repository) -> None:
    """It raises KeyError if the branch does not exist."""
    with pytest.raises(KeyError):
        repository.branches.branch("branch")


def test_branches_create_new_branch_name(repository: Repository) -> None:
    """It creates the branch with the given name."""
    main = repository.references["HEAD"].target.removeprefix("refs/heads/")
    branch = repository.branches.create("branch", repository.branches[main])
    assert "branch" == branch.name


def test_branches_create_new_branch_commit(repository: Repository) -> None:
    """It creates the branch at the given commit."""
    main = repository.references["HEAD"].target.removeprefix("refs/heads/")
    branches = repository.branches
    branch = branches.create("branch", branches[main])
    assert branches[main] == branch.commit


def test_branches_create_existing_branch(repository: Repository) -> None:
    """It raises an exception if the branch already exists."""
    main = repository.references["HEAD"].target.removeprefix("refs/heads/")
    branches = repository.branches
    branch = branches.create("branch", branches[main])
    with pytest.raises(pygit2.AlreadyExistsError):
        branches.create(branch.name, branch.commit)


def test_branches_create_existing_branch_force(repository: Repository) -> None:
    """It updates the branch head if the branch already exists."""
    main = repository.references["HEAD"].target.removeprefix("refs/heads/")
    branches = repository.branches
    branch = branches.create("branch", branches[main])
    updatefile(repository.path / "file")
    branches.create(branch.name, branches[main], force=True)
    assert branches[main] == branch.commit


def test_branches_create_default_commit(repository: Repository) -> None:
    """It creates the branch at the commit referenced by HEAD."""
    main = repository.references["HEAD"].target.removeprefix("refs/heads/")
    branches = repository.branches
    branch = branches.create("branch")
    assert branches[main] == branch.commit


def test_branches_head_name(repository: Repository) -> None:
    """It returns the branch whose name is contained in HEAD."""
    main = repository.references["HEAD"].target.removeprefix("refs/heads/")
    assert main == repository.branches.head.name


def test_branch_name_get(repository: Repository) -> None:
    """It returns the name of the branch."""
    main = repository.references["HEAD"].target.removeprefix("refs/heads/")
    branch = repository.branches.branch(main)
    assert main == branch.name


def test_branch_name_set(repository: Repository) -> None:
    """It raises AttributeError when the name is set."""
    main = repository.references["HEAD"].target.removeprefix("refs/heads/")
    branch = repository.branches.branch(main)
    with pytest.raises(AttributeError):
        branch.name = "teapot"  # type: ignore[misc]


def test_branch_commit_get(repository: Repository) -> None:
    """It returns the commit at the head of the branch."""
    main = repository.references["HEAD"].target.removeprefix("refs/heads/")
    branch = repository.branches.branch(main)
    assert repository.branches[main] == branch.commit


def test_branch_commit_set(repository: Repository) -> None:
    """It resets the branch to the given commit."""
    main = repository.references["HEAD"].target.removeprefix("refs/heads/")
    branches = repository.branches
    branches["branch"] = branches[main]
    updatefile(repository.path / "file")
    branch = branches.branch("branch")
    branch.commit = branches[main]
    assert branches[main] == branch.commit


def test_discover_fail(tmp_path: Path) -> None:
    """It returns None."""
    assert None is Repository.discover(tmp_path)


def test_path(tmp_path: Path) -> None:
    """It returns the path to the repository."""
    path = tmp_path / "repository"
    repository = Repository.init(path)
    assert path == repository.path


def test_commit_on_unborn_branch(tmp_path: Path) -> None:
    """It creates a commit without parents."""
    repository = Repository.init(tmp_path / "repository")
    repository.commit(message="initial")

    assert not repository.head.peel().parents


def test_commit_empty(repository: Repository) -> None:
    """It does not produce an empty commit (unless the branch is unborn)."""
    head = repository.head.peel()

    repository.commit(message="empty")

    assert head == repository.head.peel()


def test_commit_signature(repository: Repository) -> None:
    """It uses the provided signature."""
    (repository.path / "a").touch()

    signature = pygit2.Signature("Katherine", "katherine@example.com")
    repository.commit(message="empty", signature=signature)

    head = repository.head.peel()
    assert signature.name == head.author.name and signature.email == head.author.email


def test_commit_message_default(repository: Repository) -> None:
    """It uses an empty message by default."""
    (repository.path / "a").touch()

    repository.commit()

    head = repository.head.peel()
    assert "" == head.message


def test_createbranch_target_default(repository: Repository) -> None:
    """It creates the branch at HEAD by default."""
    repository.branches.create("branch")

    assert repository.branches["branch"] == repository.head.peel()


def test_createbranch_target_branch(repository: Repository) -> None:
    """It creates the branch at the head of the given branch."""
    main = repository.branches.head
    branch1 = repository.branches.create("branch1")

    repository.checkout(branch1)
    repository.commit()

    repository.checkout(main)
    repository.branches.create("branch2", repository.branches["branch1"])

    assert branch1.commit == repository.branches["branch2"]


def test_createbranch_target_oid(repository: Repository) -> None:
    """It creates the branch at the commit with the given OID."""
    main = repository.branches.head
    oid = main.commit.id

    repository.commit()

    repository.branches.create("branch", main.commit)

    assert oid == repository.branches["branch"].id


def test_createbranch_returns_branch(repository: Repository) -> None:
    """It returns the branch object."""
    branch = repository.branches.create("branch")
    assert branch.commit == repository.branches["branch"]


def createconflict(
    repository: Repository, path: Path, *, ours: str, theirs: str
) -> None:
    """Create an update conflict."""
    main = repository.branches.head
    update, _ = createbranches(repository, "update", "latest")

    repository.checkout(update)
    updatefile(path, theirs)

    repository.checkout(main)
    updatefile(path, ours)

    with pytest.raises(Exception, match=path.name):
        repository.cherrypick(update.commit, message="")


def test_worktree_creates_worktree(repository: Repository) -> None:
    """It creates a worktree."""
    branch = repository.branches.create("branch")

    with repository.worktree(branch) as worktree:
        assert (worktree / ".git").is_file()


def test_worktree_removes_worktree_on_exit(repository: Repository) -> None:
    """It removes the worktree on exit."""
    branch = repository.branches.create("branch")

    with repository.worktree(branch) as worktree:
        pass

    assert not worktree.is_dir()


def test_worktree_does_checkout(repository: Repository, path: Path) -> None:
    """It checks out a working tree."""
    updatefile(path)
    branch = repository.branches.create("branch")

    with repository.worktree(branch) as worktree:
        assert (worktree / path.name).is_file()


def test_worktree_no_checkout(repository: Repository, path: Path) -> None:
    """It creates a worktree without checking out the files."""
    updatefile(path)
    branch = repository.branches.create("branch")

    with repository.worktree(branch, checkout=False) as worktree:
        assert not (worktree / path.name).is_file()


def test_cherrypick_adds_file(repository: Repository, path: Path) -> None:
    """It cherry-picks the commit onto the current branch."""
    main = repository.branches.head
    branch = repository.branches.create("branch")

    repository.checkout(branch)
    updatefile(path)

    repository.checkout(main)
    assert not path.is_file()

    repository.cherrypick(branch.commit, message="")
    assert path.is_file()


def test_cherrypick_conflict_edit(repository: Repository, path: Path) -> None:
    """It raises an exception when both sides modified the file."""
    main = repository.branches.head
    branch = repository.branches.create("branch")

    repository.checkout(branch)
    updatefile(path, "a")

    repository.checkout(main)
    updatefile(path, "b")

    with pytest.raises(Exception, match=path.name):
        repository.cherrypick(branch.commit, message="")


def test_cherrypick_conflict_deletion(repository: Repository, path: Path) -> None:
    """It raises an exception when one side modified and the other deleted the file."""
    updatefile(path, "a")

    main = repository.branches.head
    branch = repository.branches.create("branch")

    repository.checkout(branch)
    updatefile(path, "b")

    repository.checkout(main)
    removefile(path)

    with pytest.raises(Exception, match=path.name):
        repository.cherrypick(branch.commit, message="")


def test_resetmerge_restores_files_with_conflicts(
    repository: Repository, path: Path
) -> None:
    """It restores the conflicting files in the working tree to our version."""
    createconflict(repository, path, ours="a", theirs="b")
    repository.resetmerge(parent="latest", cherry="update")

    assert path.read_text() == "a"


def test_resetmerge_removes_added_files(
    repository: Repository, paths: Iterator[Path]
) -> None:
    """It removes files added by the cherry-picked commit."""
    main = repository.branches.head
    update, _ = createbranches(repository, "update", "latest")
    path1, path2 = next(paths), next(paths)

    repository.checkout(update)
    updatefiles({path1: "a", path2: ""})

    repository.checkout(main)
    updatefile(path1, "b")

    with pytest.raises(Exception, match=path1.name):
        repository.cherrypick(update.commit, message="")

    repository.resetmerge(parent="latest", cherry="update")

    assert not path2.exists()


def test_resetmerge_keeps_unrelated_additions(
    repository: Repository, paths: Iterator[Path]
) -> None:
    """It keeps additions of files that did not change in the update."""
    main = repository.branches.head
    update, _ = createbranches(repository, "update", "latest")
    path1, path2 = next(paths), next(paths)

    repository.checkout(update)
    updatefile(path1, "a")

    repository.checkout(main)
    updatefile(path1, "b")

    path2.touch()

    with pytest.raises(Exception, match=path1.name):
        repository.cherrypick(update.commit, message="")

    repository.resetmerge(parent="latest", cherry="update")

    assert path2.exists()


def test_resetmerge_keeps_unrelated_changes(
    repository: Repository, paths: Iterator[Path]
) -> None:
    """It keeps modifications to files that did not change in the update."""
    main = repository.branches.head
    update, _ = createbranches(repository, "update", "latest")
    path1, path2 = next(paths), next(paths)

    repository.checkout(update)
    updatefile(path1, "a")

    repository.checkout(main)
    updatefile(path1, "b")
    updatefile(path2)

    path2.write_text("c")

    with pytest.raises(Exception, match=path1.name):
        repository.cherrypick(update.commit, message="")

    repository.resetmerge(parent="latest", cherry="update")

    assert path2.read_text() == "c"


def test_resetmerge_keeps_unrelated_deletions(
    repository: Repository, paths: Iterator[Path]
) -> None:
    """It keeps deletions of files that did not change in the update."""
    main = repository.branches.head
    update, _ = createbranches(repository, "update", "latest")
    path1, path2 = next(paths), next(paths)

    repository.checkout(update)
    updatefile(path1, "a")

    repository.checkout(main)
    updatefile(path1, "b")
    updatefile(path2)

    path2.unlink()

    with pytest.raises(Exception, match=path1.name):
        repository.cherrypick(update.commit, message="")

    repository.resetmerge(parent="latest", cherry="update")

    assert not path2.exists()


def test_resetmerge_resets_index(repository: Repository, path: Path) -> None:
    """It resets the index to HEAD, removing conflicts."""
    createconflict(repository, path, ours="a", theirs="b")

    repository.resetmerge(parent="latest", cherry="update")

    assert repository.index.write_tree() == repository.head.peel().tree.id
