"""Unit tests for cutty.projects.update."""
import dataclasses
from pathlib import Path

import pytest

from cutty.projects.repository import LATEST_BRANCH
from cutty.projects.repository import ProjectRepository
from cutty.projects.repository import UPDATE_BRANCH
from cutty.projects.template import Template
from cutty.util.git import Repository
from tests.util.git import createbranches
from tests.util.git import resolveconflicts
from tests.util.git import Side
from tests.util.git import updatefile


pytest_plugins = ["tests.fixtures.git"]


def updateproject(projectdir: Path, template: Template.Metadata) -> None:
    """Update a project by applying changes between the generated trees."""
    project = ProjectRepository(projectdir)
    with project.update(template) as outputdir:
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
    update, _ = createbranches(repository, UPDATE_BRANCH, LATEST_BRANCH)

    repository.checkout(update)
    updatefile(path, theirs)

    repository.checkout(main)
    updatefile(path, ours)

    with pytest.raises(Exception, match=path.name):
        repository.cherrypick(update.commit)


def test_continueupdate_commits_changes(repository: Repository, path: Path) -> None:
    """It commits the changes."""
    createconflict(repository, path, ours="a", theirs="b")
    resolveconflicts(repository.path, path, Side.THEIRS)

    continueupdate(repository.path)

    blob = repository.head.commit.tree / path.name
    assert blob.data == b"b"


def test_continueupdate_preserves_metainfo(repository: Repository, path: Path) -> None:
    """It preserves the original commit message."""
    createconflict(repository, path, ours="a", theirs="b")
    resolveconflicts(repository.path, path, Side.THEIRS)

    continueupdate(repository.path)

    assert repository.heads[UPDATE_BRANCH].message == repository.head.commit.message


def test_continueupdate_fastforwards_latest(repository: Repository, path: Path) -> None:
    """It updates the latest branch to the tip of the update branch."""
    createconflict(repository, path, ours="a", theirs="b")
    resolveconflicts(repository.path, path, Side.THEIRS)

    continueupdate(repository.path)

    assert repository.heads[LATEST_BRANCH] == repository.heads[UPDATE_BRANCH]


def test_continueupdate_works_after_commit(repository: Repository, path: Path) -> None:
    """It updates the latest branch even if the cherry-pick is no longer in progress."""
    createconflict(repository, path, ours="a", theirs="b")
    resolveconflicts(repository.path, path, Side.THEIRS)

    # The user invokes `git cherry-pick --continue` before `cutty update --continue`.
    repository.commit()

    continueupdate(repository.path)

    assert repository.heads[LATEST_BRANCH] == repository.heads[UPDATE_BRANCH]


def test_continueupdate_state_cleanup(repository: Repository, path: Path) -> None:
    """It removes CHERRY_PICK_HEAD."""
    createconflict(repository, path, ours="a", theirs="b")
    resolveconflicts(repository.path, path, Side.THEIRS)

    continueupdate(repository.path)

    assert repository.cherrypickhead is None


def test_skipupdate_fastforwards_latest(repository: Repository, path: Path) -> None:
    """It fast-forwards the latest branch to the tip of the update branch."""
    createconflict(repository, path, ours="a", theirs="b")

    updatehead = repository.heads[UPDATE_BRANCH]

    skipupdate(repository.path)

    assert repository.heads[LATEST_BRANCH] == updatehead


def test_abortupdate_rewinds_update_branch(repository: Repository, path: Path) -> None:
    """It resets the update branch to the tip of the latest branch."""
    createconflict(repository, path, ours="a", theirs="b")

    latesthead = repository.heads[LATEST_BRANCH]

    abortupdate(repository.path)

    assert (
        repository.heads[LATEST_BRANCH] == latesthead == repository.heads[UPDATE_BRANCH]
    )


@pytest.fixture
def project(repository: Repository) -> Repository:
    """Fixture for a project repository."""
    repository.heads.create(LATEST_BRANCH)
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
    """It includes the template name in the commit message."""
    template = dataclasses.replace(template, revision="1.0.0")

    updateproject(project.path, template)

    assert template.revision in project.head.commit.message


def test_updateproject_latest_branch(
    project: Repository, template: Template.Metadata
) -> None:
    """It updates the latest branch."""
    updatefile(project.path / "initial")

    tip = project.heads[LATEST_BRANCH]

    updateproject(project.path, template)

    assert [tip] == project.heads[LATEST_BRANCH].parents


def test_updateproject_update_branch(
    project: Repository, template: Template.Metadata
) -> None:
    """It creates the update branch."""
    updateproject(project.path, template)

    assert project.heads[LATEST_BRANCH] == project.heads[UPDATE_BRANCH]


def test_updateproject_no_changes(
    project: Repository, template: Template.Metadata
) -> None:
    """It does not create an empty commit."""
    tip = project.head.commit

    repository = ProjectRepository(project.path)
    with repository.update(template):
        pass

    assert tip == project.head.commit
