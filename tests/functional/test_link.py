"""Functional tests for `cutty link`."""
from pathlib import Path

import pytest

from cutty.projects.projectconfig import readprojectconfigfile
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


def test_non_interactive(runcutty: RunCutty, project: Path, template: Path) -> None:
    """It does not prompt for variables."""
    runcutty(
        "link",
        f"--cwd={project}",
        "--non-interactive",
        str(template),
        input="ignored\n",
    )

    assert "example" == projectvariable(project, "project")


def test_directory(runcutty: RunCutty, project: Path, template: Path) -> None:
    """It uses the template in the given subdirectory."""
    directory = "a"
    move_repository_files_to_subdirectory(template, directory)

    runcutty(
        "link", f"--cwd={project}", f"--template-directory={directory}", str(template)
    )

    config = readprojectconfigfile(project)
    assert directory == str(config.directory)


def test_revision(runcutty: RunCutty, project: Path, template: Path) -> None:
    """It uses the specified revision of the template."""
    initial = Repository.open(template).head.commit.id

    updatefile(template / "{{ cookiecutter.project }}" / "LICENSE")

    runcutty("link", f"--cwd={project}", f"--revision={initial}", str(template))
    runcutty("update", f"--cwd={project}")

    assert "LICENSE" in Repository.open(project).head.commit.tree


def test_skip(runcutty: RunCutty, project: Path, template: Path) -> None:
    """It skips an update if the revision is already linked."""
    updatefile(template / "{{ cookiecutter.project }}" / "LICENSE")

    runcutty("link", f"--cwd={project}", str(template))
    runcutty("update", f"--cwd={project}")

    assert "LICENSE" not in Repository.open(project).head.commit.tree


def test_commit_message_template(
    runcutty: RunCutty, project: Path, template: Path
) -> None:
    """It includes the template name in the commit message."""
    runcutty("link", f"--cwd={project}", str(template))

    repository = Repository.open(project)
    assert template.name in repository.head.commit.message


def test_commit_message_verb(runcutty: RunCutty, project: Path, template: Path) -> None:
    """It uses the verb 'Link' in the commit message."""
    runcutty("link", f"--cwd={project}", str(template))

    repository = Repository.open(project)
    assert "Link" in repository.head.commit.message


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


def test_empty_template(emptytemplate: Path, runcutty: RunCutty) -> None:
    """It exits with a non-zero status code."""
    (emptytemplate / "{{ cookiecutter.project }}" / "marker").touch()

    runcutty("cookiecutter", str(emptytemplate))

    (emptytemplate / "{{ cookiecutter.project }}" / "marker").unlink()

    project = Repository.init(Path("project"))
    project.commit(message="Initial")

    with pytest.raises(RunCuttyError):
        runcutty("link", "--cwd=project", str(emptytemplate))
