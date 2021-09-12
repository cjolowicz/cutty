"""Functional tests for `cutty link`."""
from pathlib import Path

import pytest

from cutty.util.git import Repository
from tests.functional.conftest import RunCutty
from tests.functional.test_update import projectvariable
from tests.util.files import chdir


def test_help(runcutty: RunCutty) -> None:
    """It exits with a status code of zero."""
    runcutty("link", "--help")


@pytest.fixture
def project(runcutty: RunCutty, template: Path) -> Path:
    """Fixture for a project."""
    runcutty("cookiecutter", str(template))

    project = Repository.init(Path("example"))
    project.commit(message="Initial")

    return project.path


def test_project_config(runcutty: RunCutty, project: Path, template: Path) -> None:
    """It adds a cutty.json to the project."""
    with chdir(project):
        runcutty("link", str(template))

    assert (project / "cutty.json").is_file()


def test_cwd(runcutty: RunCutty, project: Path, template: Path) -> None:
    """It links the project in the specified directory."""
    runcutty("link", f"--cwd={project}", str(template))

    assert (project / "cutty.json").is_file()


def test_extra_context(runcutty: RunCutty, project: Path, template: Path) -> None:
    """It allows setting variables on the command-line."""
    runcutty("link", f"--cwd={project}", str(template), "project=excellent")

    assert "excellent" == projectvariable(project, "project")
