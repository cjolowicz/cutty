"""Unit tests for cutty.projects.repository."""
import dataclasses
from collections.abc import Iterator
from pathlib import Path

import pytest

from cutty.packages.domain.package import Author
from cutty.packages.domain.package import Commit
from cutty.projects.messages import createcommitmessage
from cutty.projects.messages import updatecommitmessage
from cutty.projects.repository import ProjectRepository
from cutty.projects.template import Template
from cutty.util.git import Repository
from tests.util.git import resolveconflicts
from tests.util.git import Side
from tests.util.git import updatefile


pytest_plugins = ["tests.fixtures.git"]


def updateproject(projectdir: Path, template: Template.Metadata) -> None:
    """Update a project by applying changes between the generated trees."""
    project = ProjectRepository(projectdir)

    with project.build() as builder:
        commit = builder.commit(createcommitmessage(template))

    with project.build(parent=commit) as builder:
        (builder.path / "cutty.json").touch()
        commit2 = builder.commit(updatecommitmessage(template))

    if commit2 != commit:
        project.import_(commit2)


def continue_(projectdir: Path) -> None:
    """Continue an update after conflict resolution."""
    project = ProjectRepository(projectdir)
    project.continue_()


def abort(projectdir: Path) -> None:
    """Abort an update with conflicts."""
    project = ProjectRepository(projectdir)
    project.abort()


def createconflict(
    repository: Repository, path: Path, *, ours: str, theirs: str
) -> None:
    """Create an update conflict."""
    main = repository.head
    branch = repository.heads.create("branch")

    repository.checkout(branch)
    updatefile(path, theirs)

    repository.checkout(main)
    updatefile(path, ours)

    cherry = repository.heads.pop(branch.name)

    with pytest.raises(Exception, match=path.name):
        repository.cherrypick(cherry)


def test_continue_commits_changes(repository: Repository, path: Path) -> None:
    """It commits the changes."""
    createconflict(repository, path, ours="a", theirs="b")
    resolveconflicts(repository.path, path, Side.THEIRS)

    continue_(repository.path)

    blob = repository.head.commit.tree / path.name
    assert blob.data == b"b"


def test_continue_state_cleanup(repository: Repository, path: Path) -> None:
    """It removes CHERRY_PICK_HEAD."""
    createconflict(repository, path, ours="a", theirs="b")
    resolveconflicts(repository.path, path, Side.THEIRS)

    continue_(repository.path)

    assert repository.cherrypickhead is None


def test_continue_untracked(repository: Repository, path: Path) -> None:
    """It does not commit untracked files."""
    createconflict(repository, path, ours="a", theirs="b")
    resolveconflicts(repository.path, path, Side.THEIRS)

    untracked = repository.path / "untracked"
    untracked.touch()

    continue_(repository.path)

    assert untracked.name not in repository.head.commit.tree


def test_continue_dirty(repository: Repository, paths: Iterator[Path]) -> None:
    """It does not commit local modifications."""
    dirty, path = next(paths), next(paths)

    updatefile(dirty)

    createconflict(repository, path, ours="a", theirs="b")
    resolveconflicts(repository.path, path, Side.THEIRS)

    dirty.write_text("local modification")

    continue_(repository.path)

    blob = repository.head.commit.tree / dirty.name
    assert not blob.data


def test_abort(repository: Repository, path: Path) -> None:
    """It uses our version."""
    createconflict(repository, path, ours="a", theirs="b")

    abort(repository.path)

    blob = repository.head.commit.tree / path.name
    assert blob.data.decode() == "a"


@pytest.fixture
def project(repository: Repository) -> Repository:
    """Fixture for a project repository."""
    return repository


def test_updateproject_commit(project: Repository, template: Template.Metadata) -> None:
    """It creates a commit on the current branch."""
    tip = project.head.commit

    updateproject(project.path, template)

    assert [tip] == project.head.commit.parents


def test_updateproject_commit_message(
    project: Repository, template: Template.Metadata
) -> None:
    """It uses a commit message indicating an update."""
    updateproject(project.path, template)

    assert "update" in project.head.commit.message.lower()


def test_updateproject_commit_message_template(
    project: Repository, template: Template.Metadata
) -> None:
    """It includes the template name in the commit message."""
    updateproject(project.path, template)

    assert template.name in project.head.commit.message


def test_updateproject_commit_message_revision(
    project: Repository, template: Template.Metadata
) -> None:
    """It includes the template revision in the commit message."""
    commit = Commit(
        "f4c0629d635865697b3e99b5ca581e78b2c7d976",
        "v1.0.0",
        "Release 1.0.0",
        Author("You", "you@example.com"),
    )
    template = dataclasses.replace(template, commit2=commit)

    updateproject(project.path, template)

    assert template.commit2 and template.commit2.revision in project.head.commit.message


def test_updateproject_no_changes(
    project: Repository, template: Template.Metadata
) -> None:
    """It does not create an empty commit."""
    tip = project.head.commit

    repository = ProjectRepository(project.path)

    with repository.build() as builder:
        commit = builder.commit(createcommitmessage(template))

    with repository.build(parent=commit) as builder:
        commit2 = builder.commit(updatecommitmessage(template))

    if commit2 != commit:
        repository.import_(commit2)

    assert tip == project.head.commit
