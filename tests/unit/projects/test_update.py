"""Unit tests for cutty.projects.repository."""
import dataclasses
from pathlib import Path

import pytest

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

    with project.reset(template) as (outputdir, getlatest):
        pass

    with project.update(template, parent=getlatest()) as outputdir:
        (outputdir / "cutty.json").touch()


def continueupdate(projectdir: Path) -> None:
    """Continue an update after conflict resolution."""
    project = ProjectRepository(projectdir)
    project.continueupdate()


def skipupdate(projectdir: Path) -> None:
    """Skip an update with conflicts."""
    project = ProjectRepository(projectdir)
    project.skipupdate()


def abortupdate(projectdir: Path) -> None:
    """Abort an update with conflicts."""
    project = ProjectRepository(projectdir)
    project.abortupdate()


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

    with pytest.raises(Exception, match=path.name):
        repository.cherrypick(branch.commit)


def test_continueupdate_commits_changes(repository: Repository, path: Path) -> None:
    """It commits the changes."""
    createconflict(repository, path, ours="a", theirs="b")
    resolveconflicts(repository.path, path, Side.THEIRS)

    continueupdate(repository.path)

    blob = repository.head.commit.tree / path.name
    assert blob.data == b"b"


def test_continueupdate_works_after_commit(repository: Repository, path: Path) -> None:
    """It continues the update even if the cherry-pick is no longer in progress."""
    createconflict(repository, path, ours="a", theirs="b")
    resolveconflicts(repository.path, path, Side.THEIRS)

    # The user invokes `git cherry-pick --continue` before `cutty update --continue`.
    repository.commit()

    continueupdate(repository.path)

    blob = repository.head.commit.tree / path.name
    assert blob.data.decode() == "b"


def test_continueupdate_state_cleanup(repository: Repository, path: Path) -> None:
    """It removes CHERRY_PICK_HEAD."""
    createconflict(repository, path, ours="a", theirs="b")
    resolveconflicts(repository.path, path, Side.THEIRS)

    continueupdate(repository.path)

    assert repository.cherrypickhead is None


def test_skipupdate(repository: Repository, path: Path) -> None:
    """It uses our version."""
    updatefile(repository.path / "cutty.json")
    createconflict(repository, path, ours="a", theirs="b")

    skipupdate(repository.path)

    blob = repository.head.commit.tree / path.name
    assert blob.data.decode() == "a"


def test_abortupdate(repository: Repository, path: Path) -> None:
    """It uses our version."""
    createconflict(repository, path, ours="a", theirs="b")

    abortupdate(repository.path)

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
    template = dataclasses.replace(template, revision="1.0.0")

    updateproject(project.path, template)

    assert template.revision in project.head.commit.message


def test_updateproject_no_changes(
    project: Repository, template: Template.Metadata
) -> None:
    """It does not create an empty commit."""
    tip = project.head.commit

    repository = ProjectRepository(project.path)

    with repository.reset(template) as (outputdir, getlatest):
        pass

    with repository.update(template, parent=getlatest()):
        pass

    assert tip == project.head.commit
