"""Functional tests for `cutty import`."""
from pathlib import Path

import pytest

from cutty.util.git import Repository
from tests.functional.conftest import RunCutty
from tests.util.files import chdir
from tests.util.git import updatefile


def test_help(runcutty: RunCutty) -> None:
    """It exits with a status code of zero."""
    runcutty("import", "--help")


@pytest.fixture
def project(runcutty: RunCutty, template: Path) -> Path:
    """Fixture for a generated project."""
    runcutty("create", "--non-interactive", str(template))

    return Path("example")


def test_noop(runcutty: RunCutty, project: Path) -> None:
    """It doesn't do anything if nothing changed."""
    head = Repository.open(project).head.commit

    with chdir(project):
        runcutty("import")

    assert head == Repository.open(project).head.commit


@pytest.fixture
def templateproject(template: Path) -> Path:
    """Return the project directory in the template."""
    return template / "{{ cookiecutter.project }}"


def test_latest(runcutty: RunCutty, templateproject: Path, project: Path) -> None:
    """It applies the latest changeset by default."""
    updatefile(templateproject / "marker")

    with chdir(project):
        runcutty("import")

    assert "marker" in Repository.open(project).head.commit.tree


def test_revision(
    runcutty: RunCutty, template: Path, templateproject: Path, project: Path
) -> None:
    """It applies the indicated changeset."""
    updatefile(templateproject / "marker")

    revision = Repository.open(template).head.commit.id

    with chdir(project):
        runcutty("import", f"--revision={revision}")

    assert "marker" in Repository.open(project).head.commit.tree


def test_parent(
    runcutty: RunCutty, template: Path, templateproject: Path, project: Path
) -> None:
    """It does not apply the parent commit."""
    updatefile(templateproject / "extra")
    updatefile(templateproject / "marker")

    with chdir(project):
        runcutty("import")

    assert "marker" in Repository.open(project).head.commit.tree
    assert "extra" not in Repository.open(project).head.commit.tree
