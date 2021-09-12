"""Functional tests for `cutty link`."""
from pathlib import Path

import pytest

from cutty.filestorage.adapters.observers.git import LATEST_BRANCH
from cutty.templates.adapters.cookiecutter.projectconfig import readprojectconfigfile
from cutty.util.git import Repository
from tests.functional.conftest import RunCutty
from tests.functional.test_update import projectvariable
from tests.util.files import chdir
from tests.util.git import move_repository_files_to_subdirectory
from tests.util.git import updatefile


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


def test_no_input(runcutty: RunCutty, project: Path, template: Path) -> None:
    """It does not prompt for variables."""
    runcutty("link", f"--cwd={project}", "--no-input", str(template), input="ignored\n")

    assert "example" == projectvariable(project, "project")


def test_directory(runcutty: RunCutty, project: Path, template: Path) -> None:
    """It uses the template in the given subdirectory."""
    directory = "a"
    move_repository_files_to_subdirectory(template, directory)

    runcutty("link", f"--cwd={project}", f"--directory={directory}", str(template))

    config = readprojectconfigfile(project)
    assert directory == str(config.directory)


def test_checkout(runcutty: RunCutty, project: Path, template: Path) -> None:
    """It uses the specified revision of the template."""
    initial = Repository.open(template).head.commit.id

    updatefile(template / "{{ cookiecutter.project }}" / "LICENSE")

    runcutty("link", f"--cwd={project}", f"--checkout={initial}", str(template))

    latest = Repository.open(project).branch(LATEST_BRANCH)
    assert "LICENSE" not in latest.commit.tree
