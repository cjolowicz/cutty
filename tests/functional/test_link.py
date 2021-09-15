"""Functional tests for `cutty link`."""
from pathlib import Path

import pytest

from cutty.filestorage.adapters.observers.git import LATEST_BRANCH
from cutty.filestorage.adapters.observers.git import UPDATE_BRANCH
from cutty.templates.adapters.cookiecutter.projectconfig import readprojectconfigfile
from cutty.util.git import Repository
from tests.functional.conftest import RunCutty
from tests.functional.conftest import RunCuttyError
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


def test_update_branch_exists(
    runcutty: RunCutty, project: Path, template: Path
) -> None:
    """It updates an existing update branch."""
    repository = Repository.open(project)
    for branch in UPDATE_BRANCH, LATEST_BRANCH:
        repository.heads.create(branch)

    updatefile(project / "marker")

    runcutty("link", f"--cwd={project}", str(template))

    assert (project / "marker").is_file()
    assert (project / "cutty.json").is_file()


def test_latest_branch_exists(
    runcutty: RunCutty, project: Path, template: Path
) -> None:
    """It fast-forwards an existing latest branch."""
    repository = Repository.open(project)
    _, latest = [
        repository.heads.create(branch) for branch in (UPDATE_BRANCH, LATEST_BRANCH)
    ]
    expected = latest.commit

    updatefile(project / "marker")

    runcutty("link", f"--cwd={project}", str(template))

    [actual] = latest.commit.parents
    assert expected == actual


def test_commit_message(runcutty: RunCutty, project: Path, template: Path) -> None:
    """It includes the template name in the commit message."""
    runcutty("link", f"--cwd={project}", str(template))

    repository = Repository.open(project)
    assert template.name in repository.head.commit.message


def test_legacy_project_config_bindings(runcutty: RunCutty, template: Path) -> None:
    """It reads bindings from .cookiecutter.json if it exists."""
    updatefile(
        template / "{{ cookiecutter.project }}" / ".cookiecutter.json",
        "{{ cookiecutter | jsonify }}",
    )

    project = Path("bespoke-project")

    runcutty("cookiecutter", str(template), f"project={project}")

    Repository.init(project).commit(message="Initial")

    runcutty("link", f"--cwd={project}", str(template))

    assert project.name == projectvariable(project, "project")


def test_legacy_project_config_template(runcutty: RunCutty, template: Path) -> None:
    """It reads the template from .cookiecutter.json if it exists."""
    updatefile(
        template / "{{ cookiecutter.project }}" / ".cookiecutter.json",
        "{{ cookiecutter | jsonify }}",
    )

    runcutty("cookiecutter", str(template))

    project = Repository.init(Path("example"))
    project.commit(message="Initial")

    runcutty("link", f"--cwd={project.path}")


def test_template_not_specified(
    runcutty: RunCutty, project: Path, template: Path
) -> None:
    """It exits with an error."""
    with pytest.raises(RunCuttyError):
        runcutty("link", f"--cwd={project}")
