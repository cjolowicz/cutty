"""Functional tests for `cutty import`."""
from pathlib import Path

import pygit2
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


def commit(repository: Path) -> pygit2.Commit:
    """Return the commit referenced by HEAD."""
    return Repository.open(repository).head.commit


def test_noop(runcutty: RunCutty, project: Path) -> None:
    """It doesn't do anything if the project is up-to-date."""
    head = commit(project)

    with chdir(project):
        runcutty("import")

    assert head == commit(project)


@pytest.fixture
def templateproject(template: Path) -> Path:
    """Return the project directory in the template."""
    return template / "{{ cookiecutter.project }}"


def tree(repository: Path) -> pygit2.Tree:
    """Return the tree referenced by HEAD."""
    return commit(repository).tree


def test_latest(runcutty: RunCutty, templateproject: Path, project: Path) -> None:
    """It applies the latest changeset by default."""
    updatefile(templateproject / "marker")

    with chdir(project):
        runcutty("import")

    assert "marker" in tree(project)


def test_idempotent(runcutty: RunCutty, templateproject: Path, project: Path) -> None:
    """It doesn't do anything if the change was already imported."""
    updatefile(templateproject / "marker")

    with chdir(project):
        runcutty("import")

    head = commit(project)

    with chdir(project):
        runcutty("import")

    assert head == commit(project)


def test_revision(
    runcutty: RunCutty, template: Path, templateproject: Path, project: Path
) -> None:
    """It applies the indicated changeset."""
    updatefile(templateproject / "marker")

    revision = commit(template).id

    with chdir(project):
        runcutty("import", f"--revision={revision}")

    assert "marker" in tree(project)


def test_parent(
    runcutty: RunCutty, template: Path, templateproject: Path, project: Path
) -> None:
    """It does not apply the parent commit."""
    updatefile(templateproject / "extra")
    updatefile(templateproject / "marker")

    with chdir(project):
        runcutty("import")

    assert "marker" in tree(project)
    assert "extra" not in tree(project)


def test_child(
    runcutty: RunCutty, template: Path, templateproject: Path, project: Path
) -> None:
    """It does not apply the child commit."""
    updatefile(templateproject / "marker")
    updatefile(templateproject / "extra")

    with chdir(project):
        runcutty("import", "--revision=HEAD^")

    assert "marker" in tree(project)
    assert "extra" not in tree(project)


def test_conflict(runcutty: RunCutty, templateproject: Path, project: Path) -> None:
    """It exits with non-zero status on merge conflicts."""
    updatefile(templateproject / "marker", "a")
    updatefile(project / "marker", "b")

    with pytest.raises(Exception, match="conflict"):
        with chdir(project):
            runcutty("import")


def test_conflict_message(
    runcutty: RunCutty, templateproject: Path, project: Path
) -> None:
    """It does not report cutty.json on merge conflicts."""
    updatefile(templateproject / "extra")
    updatefile(templateproject / "marker", "a")
    updatefile(project / "marker", "b")

    with pytest.raises(Exception) as exceptioninfo:
        with chdir(project):
            runcutty("import")

    assert "cutty.json" not in str(exceptioninfo.value)


def test_no_vcs(runcutty: RunCutty, template: Path, templateproject: Path) -> None:
    """It returns with non-zero status if the template has no version history."""
    location = "local+{}".format(template.as_uri())

    runcutty("create", "--non-interactive", location)

    project = Path("example")

    updatefile(templateproject / "marker")

    with pytest.raises(Exception, match="not support"):
        with chdir(project):
            runcutty("import")
