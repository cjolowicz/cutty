"""Unit tests for cutty.util.git."""
from collections.abc import Iterator
from pathlib import Path

import pygit2
import pytest

from cutty.util.git import MergeConflictError
from cutty.util.git import Repository
from tests.util.git import createbranches
from tests.util.git import removefile
from tests.util.git import updatefile
from tests.util.git import updatefiles


pytest_plugins = ["tests.fixtures.git"]


def test_heads_len_empty(tmp_path: Path) -> None:
    """It returns zero if there are no heads."""
    repository = Repository.init(tmp_path / "repository")
    assert not len(repository.heads)


def test_heads_len_nonzero(repository: Repository) -> None:
    """It returns the number of heads."""
    assert 1 == len(repository.heads)


def test_heads_bool_empty(tmp_path: Path) -> None:
    """It returns False if there are no heads."""
    repository = Repository.init(tmp_path / "repository")
    assert not repository.heads


def test_heads_bool_nonzero(repository: Repository) -> None:
    """It returns True if there is a head."""
    assert repository.heads


def test_heads_contains_false(repository: Repository) -> None:
    """It returns False if the head does not exist."""
    assert "branch" not in repository.heads


def test_heads_contains_true(repository: Repository) -> None:
    """It returns True if the head exists."""
    assert repository.head.name in repository.heads


def test_heads_iter(repository: Repository) -> None:
    """It yields the name of each branch."""
    head = repository.head
    assert [head.name] == list(iter(repository.heads))


def test_heads_getitem_fail(repository: Repository) -> None:
    """It raises KeyError."""
    with pytest.raises(KeyError):
        repository.heads["branch"]


def test_heads_getitem_pass(repository: Repository) -> None:
    """It returns the commit at the head of the branch."""
    head = repository.head
    assert head.commit == repository.heads[head.name]


def test_heads_setitem_new(repository: Repository) -> None:
    """It creates a branch pointing to the given commit."""
    repository.heads["branch"] = repository.head.commit
    assert repository.head.commit == repository.heads["branch"]


def test_heads_setitem_existing(repository: Repository) -> None:
    """It resets the branch to the given commit."""
    head, heads = repository.head, repository.heads
    heads["branch"] = head.commit
    updatefile(repository.path / "file")
    heads["branch"] = head.commit
    assert head.commit == heads["branch"]


def test_heads_delitem_fail(repository: Repository) -> None:
    """It raises KeyError."""
    with pytest.raises(KeyError):
        del repository.heads["branch"]


def test_heads_delitem_pass(repository: Repository) -> None:
    """It removes the branch."""
    head, heads = repository.head, repository.heads
    heads["branch"] = head.commit
    del heads["branch"]
    assert "branch" not in heads


def test_heads_keys(repository: Repository) -> None:
    """It returns the branch names."""
    [branch] = repository.heads.keys()
    assert repository.head.name == branch


def test_heads_pop_returns_commit(repository: Repository) -> None:
    """It removes the branch and returns the commit at its head."""
    heads = repository.heads
    heads["branch"] = repository.head.commit
    commit = heads.pop("branch")
    assert repository.head.commit == commit


def test_heads_pop_removes_branch(repository: Repository) -> None:
    """It removes the branch and returns the commit at its head."""
    heads = repository.heads
    heads["branch"] = repository.head.commit
    heads.pop("branch")
    assert "branch" not in heads


def test_branch_fail(repository: Repository) -> None:
    """It raises KeyError if the branch does not exist."""
    with pytest.raises(KeyError):
        repository.branch("branch")


def test_heads_create_new_branch_name(repository: Repository) -> None:
    """It creates the branch with the given name."""
    branch = repository.heads.create("branch", repository.head.commit)
    assert "branch" == branch.name


def test_heads_create_new_branch_commit(repository: Repository) -> None:
    """It creates the branch at the given commit."""
    branch = repository.heads.create("branch", repository.head.commit)
    assert repository.head.commit == branch.commit


def test_heads_create_new_branch_at_ancestor(repository: Repository) -> None:
    """It creates the branch at an earlier commit."""
    parent = repository.head.commit
    updatefile(repository.path / "a")
    branch = repository.heads.create("branch", parent)
    assert parent == branch.commit


def test_heads_create_new_branch_at_another_branch(repository: Repository) -> None:
    """It creates the branch at a commit on another branch."""
    main = repository.head
    branch1 = repository.heads.create("branch1")

    repository.checkout(branch1)
    repository.commit()

    repository.checkout(main)
    branch2 = repository.heads.create("branch2", branch1.commit)

    assert branch1.commit == branch2.commit


def test_heads_create_existing_branch(repository: Repository) -> None:
    """It raises an exception if the branch already exists."""
    heads = repository.heads
    branch = heads.create("branch", repository.head.commit)
    with pytest.raises(pygit2.AlreadyExistsError):
        heads.create(branch.name, branch.commit)


def test_heads_create_existing_branch_force(repository: Repository) -> None:
    """It updates the branch head if the branch already exists."""
    head, heads = repository.head, repository.heads
    branch = heads.create("branch", head.commit)
    updatefile(repository.path / "a")
    heads.create(branch.name, head.commit, force=True)
    assert head.commit == branch.commit


def test_heads_create_default_commit(repository: Repository) -> None:
    """It creates the branch at the commit referenced by HEAD."""
    branch = repository.heads.create("branch")
    assert branch.commit == repository.head.commit


def test_head_name(repository: Repository) -> None:
    """It returns the branch whose name is contained in HEAD."""
    head = repository._repository.references["HEAD"]
    name = head.target.removeprefix("refs/heads/")
    assert name == repository.head.name


def test_head_detached(repository: Repository) -> None:
    """It raises an exception if the HEAD is detached."""
    repository._repository.set_head(repository.head.commit.id)
    with pytest.raises(ValueError):
        repository.head


def test_branch_name_get(repository: Repository) -> None:
    """It returns the name of the branch."""
    branch = repository.branch(repository.head.name)
    assert repository.head.name == branch.name


def test_branch_name_set(repository: Repository) -> None:
    """It raises AttributeError when the name is set."""
    branch = repository.head
    with pytest.raises(AttributeError):
        branch.name = "teapot"  # type: ignore[misc]


def test_branch_commit_get(repository: Repository) -> None:
    """It returns the commit at the head of the branch."""
    branch = repository.head
    assert repository.heads[branch.name] == branch.commit


def test_branch_commit_set(repository: Repository) -> None:
    """It resets the branch to the given commit."""
    head, heads = repository.head, repository.heads
    heads["branch"] = head.commit
    updatefile(repository.path / "a")
    branch = repository.branch("branch")
    branch.commit = head.commit
    assert head.commit == branch.commit


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

    assert not repository.head.commit.parents


def test_commit_empty(repository: Repository) -> None:
    """It does not produce an empty commit (unless the branch is unborn)."""
    head = repository.head.commit

    repository.commit(message="empty")

    assert head == repository.head.commit


def test_commit_author(repository: Repository) -> None:
    """It uses the provided author."""
    (repository.path / "a").touch()

    author = pygit2.Signature("Katherine", "katherine@example.com")
    repository.commit(message="empty", author=author)

    head = repository.head.commit
    assert author.name == head.author.name and author.email == head.author.email


def test_commit_committer(repository: Repository) -> None:
    """It uses the provided signature."""
    (repository.path / "a").touch()

    committer = pygit2.Signature("Katherine", "katherine@example.com")
    repository.commit(message="empty", committer=committer)

    head = repository.head.commit
    assert (
        committer.name == head.committer.name
        and committer.email == head.committer.email
    )


def test_commit_message_default(repository: Repository) -> None:
    """It uses an empty message by default."""
    (repository.path / "a").touch()

    repository.commit()

    head = repository.head.commit
    assert "" == head.message


def createconflict(
    repository: Repository, path: Path, *, ours: str, theirs: str
) -> None:
    """Create an update conflict."""
    main = repository.head
    update, _ = createbranches(repository, "update", "latest")

    repository.checkout(update)
    updatefile(path, theirs)

    repository.checkout(main)
    updatefile(path, ours)

    with pytest.raises(MergeConflictError, match=path.name):
        repository.cherrypick(update.commit)


def test_worktree_creates_worktree(repository: Repository) -> None:
    """It creates a worktree."""
    branch = repository.heads.create("branch")

    with repository.worktree(branch) as worktree:
        assert (worktree.path / ".git").is_file()


def test_worktree_removes_worktree_on_exit(repository: Repository) -> None:
    """It removes the worktree on exit."""
    branch = repository.heads.create("branch")

    with repository.worktree(branch) as worktree:
        pass

    assert not worktree.path.is_dir()


def test_worktree_prunes_worktree_on_failure(repository: Repository) -> None:
    """It removes the administrative files for the worktree on failure."""
    branch = repository.heads.create("branch")

    with pytest.raises(Exception, match="Boom"):
        with repository.worktree(branch) as worktree:
            raise Exception("Boom")

    privatedir = repository.path / ".git" / "worktrees" / worktree.path.name
    assert not privatedir.exists()


def test_worktree_does_checkout(repository: Repository, path: Path) -> None:
    """It checks out a working tree."""
    updatefile(path)
    branch = repository.heads.create("branch")

    with repository.worktree(branch) as worktree:
        assert (worktree.path / path.name).is_file()


def test_worktree_no_checkout(repository: Repository, path: Path) -> None:
    """It creates a worktree without checking out the files."""
    updatefile(path)
    branch = repository.heads.create("branch")

    with repository.worktree(branch, checkout=False) as worktree:
        assert not (worktree.path / path.name).is_file()


def test_worktree_tempfile_failure(
    repository: Repository, monkeypatch: pytest.MonkeyPatch
) -> None:
    """It does not crash when `tempfile` fails."""
    import tempfile

    def raise_() -> None:
        raise Exception("boom")

    monkeypatch.setattr(tempfile, "TemporaryDirectory", raise_)
    branch = repository.heads.create("branch")

    with pytest.raises(Exception, match="boom"):
        with repository.worktree(branch, checkout=False):
            pass


def test_cherrypick_adds_file(repository: Repository, path: Path) -> None:
    """It cherry-picks the commit onto the current branch."""
    main = repository.head
    branch = repository.heads.create("branch")

    repository.checkout(branch)
    updatefile(path)

    repository.checkout(main)
    assert not path.is_file()

    repository.cherrypick(branch.commit)
    assert path.is_file()


def test_cherrypick_message(repository: Repository, path: Path) -> None:
    """It uses the original commit message."""
    main = repository.head
    branch = repository.heads.create("branch")

    repository.checkout(branch)
    updatefile(path)
    message = repository.head.commit.message

    repository.checkout(main)
    repository.cherrypick(branch.commit)

    assert message == repository.head.commit.message


def test_cherrypick_author(repository: Repository) -> None:
    """It uses the original commit author."""
    main = repository.head
    branch = repository.heads.create("branch")
    author = pygit2.Signature("author", "author@example.com")

    repository.checkout(branch)
    (repository.path / "a").touch()
    repository.commit(author=author)

    repository.checkout(main)
    repository.cherrypick(branch.commit)

    assert author.email == repository.head.commit.author.email


def test_cherrypick_committer(
    repository: Repository, monkeypatch: pytest.MonkeyPatch
) -> None:
    """It creates its own committer signature."""
    main = repository.head
    branch = repository.heads.create("branch")
    committer = pygit2.Signature("committer", "committer@example.com")

    repository.checkout(branch)
    (repository.path / "a").touch()
    repository.commit(committer=committer)

    cherrypicker = pygit2.Signature("cherrypicker", "cherrypicker@example.com")
    monkeypatch.setenv("GIT_AUTHOR_NAME", cherrypicker.name)
    monkeypatch.setenv("GIT_AUTHOR_EMAIL", cherrypicker.email)

    repository.checkout(main)
    repository.cherrypick(branch.commit)

    assert cherrypicker.email == repository.head.commit.committer.email


def test_cherrypick_conflict_edit(repository: Repository, path: Path) -> None:
    """It raises an exception when both sides modified the file."""
    main = repository.head
    branch = repository.heads.create("branch")

    repository.checkout(branch)
    updatefile(path, "a")

    repository.checkout(main)
    updatefile(path, "b")

    with pytest.raises(MergeConflictError, match=path.name):
        repository.cherrypick(branch.commit)


def test_cherrypick_conflict_deletion(repository: Repository, path: Path) -> None:
    """It raises an exception when one side modified and the other deleted the file."""
    updatefile(path, "a")

    main = repository.head
    branch = repository.heads.create("branch")

    repository.checkout(branch)
    updatefile(path, "b")

    repository.checkout(main)
    removefile(path)

    with pytest.raises(MergeConflictError, match=path.name):
        repository.cherrypick(branch.commit)


def test_cherrypickhead_none(repository: Repository) -> None:
    """It returns None if no cherry pick is in progress."""
    assert repository.cherrypickhead is None


def test_cherrypickhead_progress(repository: Repository, path: Path) -> None:
    """It returns the commit being cherry-picked."""
    createconflict(repository, path, ours="a", theirs="b")

    assert repository.cherrypickhead == repository.heads["update"]


def test_resetcherrypick_restores_files_with_conflicts(
    repository: Repository, path: Path
) -> None:
    """It restores the conflicting files in the working tree to our version."""
    createconflict(repository, path, ours="a", theirs="b")
    repository.resetcherrypick()

    assert path.read_text() == "a"


def test_resetcherrypick_removes_added_files(
    repository: Repository, paths: Iterator[Path]
) -> None:
    """It removes files added by the cherry-picked commit."""
    main = repository.head
    update, _ = createbranches(repository, "update", "latest")
    path1, path2 = next(paths), next(paths)

    repository.checkout(update)
    updatefiles({path1: "a", path2: ""})

    repository.checkout(main)
    updatefile(path1, "b")

    with pytest.raises(MergeConflictError, match=path1.name):
        repository.cherrypick(update.commit)

    repository.resetcherrypick()

    assert not path2.exists()


def test_resetcherrypick_keeps_unrelated_additions(
    repository: Repository, paths: Iterator[Path]
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

    with pytest.raises(MergeConflictError, match=path1.name):
        repository.cherrypick(update.commit)

    repository.resetcherrypick()

    assert path2.exists()


def test_resetcherrypick_keeps_unrelated_changes(
    repository: Repository, paths: Iterator[Path]
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

    with pytest.raises(MergeConflictError, match=path1.name):
        repository.cherrypick(update.commit)

    repository.resetcherrypick()

    assert path2.read_text() == "c"


def test_resetcherrypick_keeps_unrelated_deletions(
    repository: Repository, paths: Iterator[Path]
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

    with pytest.raises(MergeConflictError, match=path1.name):
        repository.cherrypick(update.commit)

    repository.resetcherrypick()

    assert not path2.exists()


def test_resetcherrypick_resets_index(repository: Repository, path: Path) -> None:
    """It resets the index to HEAD, removing conflicts."""
    createconflict(repository, path, ours="a", theirs="b")

    repository.resetcherrypick()

    index = repository._repository.index
    assert index.write_tree() == repository.head.commit.tree.id


def test_resetcherrypick_state_cleanup(repository: Repository, path: Path) -> None:
    """It removes CHERRY_PICK_HEAD."""
    createconflict(repository, path, ours="a", theirs="b")

    assert repository.cherrypickhead

    repository.resetcherrypick()

    assert not repository.cherrypickhead


def test_resetcherrypick_idempotent(repository: Repository, path: Path) -> None:
    """It is idempotent."""
    createconflict(repository, path, ours="a", theirs="b")

    repository.resetcherrypick()
    repository.resetcherrypick()
