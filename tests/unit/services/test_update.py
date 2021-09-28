"""Unit tests for cutty.services.update."""
import dataclasses
from pathlib import Path

import pytest

from cutty.filesystems.adapters.dict import DictFilesystem
from cutty.filesystems.domain.path import Path as VirtualPath
from cutty.projects.create import CreateProject
from cutty.projects.create import LATEST_BRANCH
from cutty.projects.create import UPDATE_BRANCH
from cutty.repositories.domain.repository import Repository as Template
from cutty.services.update import abortupdate
from cutty.services.update import continueupdate
from cutty.services.update import skipupdate
from cutty.services.update import updateproject
from cutty.util.git import Repository
from tests.util.git import createbranches
from tests.util.git import resolveconflicts
from tests.util.git import Side
from tests.util.git import updatefile


pytest_plugins = ["tests.fixtures.git"]


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


@pytest.fixture
def template() -> Template:
    """Fixture for a `Template` instance."""
    templatepath = VirtualPath(filesystem=DictFilesystem({}))
    return Template("template", templatepath, None)


@pytest.fixture
def createproject(template: Template) -> CreateProject:
    """Fixture for a `createproject` function."""

    def _(project: Path) -> Template:
        (project / "marker").touch()
        return template

    return _


def test_updateproject_commit(
    project: Repository, createproject: CreateProject
) -> None:
    """It creates a commit on the current branch."""
    tip = project.head.commit

    updateproject(project.path, createproject)

    assert [tip] == project.head.commit.parents


def test_updateproject_commit_message(
    project: Repository, createproject: CreateProject
) -> None:
    """It uses a commit message indicating an update."""
    updateproject(project.path, createproject)

    assert "update" in project.head.commit.message.lower()


def test_updateproject_commit_message_template(
    project: Repository, createproject: CreateProject, template: Template
) -> None:
    """It includes the template name in the commit message."""
    updateproject(project.path, createproject)

    assert template.name in project.head.commit.message


def test_updateproject_commit_message_revision(
    project: Repository, template: Template
) -> None:
    """It includes the template name in the commit message."""
    template = dataclasses.replace(template, revision="1.0.0")

    def createproject(project: Path) -> Template:
        (project / "marker").touch()
        return template

    updateproject(project.path, createproject)

    assert template.revision in project.head.commit.message


def test_updateproject_latest_branch(
    project: Repository, createproject: CreateProject
) -> None:
    """It updates the latest branch."""
    updatefile(project.path / "initial")

    tip = project.heads[LATEST_BRANCH]

    updateproject(project.path, createproject)

    assert [tip] == project.heads[LATEST_BRANCH].parents


def test_updateproject_update_branch(
    project: Repository, createproject: CreateProject
) -> None:
    """It creates the update branch."""
    updateproject(project.path, createproject)

    assert project.heads[LATEST_BRANCH] == project.heads[UPDATE_BRANCH]


def test_updateproject_no_changes(project: Repository, template: Template) -> None:
    """It does not create an empty commit."""
    tip = project.head.commit

    updateproject(project.path, lambda _: template)

    assert tip == project.head.commit
