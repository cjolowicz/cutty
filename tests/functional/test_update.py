"""Functional tests for the update CLI."""
import json
from pathlib import Path
from typing import Any

import pygit2
import pytest

from tests.functional.conftest import RunCutty
from tests.util.files import chdir
from tests.util.git import removefile
from tests.util.git import updatefile


def test_help(runcutty: RunCutty) -> None:
    """It exits with a status code of zero."""
    runcutty("update", "--help")


@pytest.fixture
def project(runcutty: RunCutty, repository: Path) -> Path:
    """Fixture for a generated project."""
    project = Path("awesome")

    runcutty("create", "--no-input", str(repository), f"project={project.name}")

    return project


def addprojectvariable(repository: Path, name: str, value: Any) -> None:
    """Add a project variable to the template."""
    path = repository / "cookiecutter.json"
    data = json.loads(path.read_text())
    data[name] = value
    updatefile(path, json.dumps(data))


def projectvariable(project: Path, name: str) -> Any:
    """Return the bound value of a project variable."""
    path = project / ".cookiecutter.json"
    data = json.loads(path.read_text())
    return data[name]


def test_update_trivial(runcutty: RunCutty, repository: Path, project: Path) -> None:
    """It applies changes from the template."""
    updatefile(
        repository / "{{ cookiecutter.project }}" / "README.md",
        """
        # {{ cookiecutter.project }}
        An awesome project.
        """,
    )

    with chdir(project):
        runcutty("update")

    assert (project / "README.md").read_text() == "# awesome\nAn awesome project.\n"


def test_update_merge(runcutty: RunCutty, repository: Path, project: Path) -> None:
    """It merges changes from the template."""
    updatefile(
        project / "README.md",
        """
        # awesome
        An awesome project.
        """,
    )

    updatefile(
        repository / "{{ cookiecutter.project }}" / "LICENSE",
        "",
    )

    with chdir(project):
        runcutty("update")

    assert (project / "README.md").read_text() == "# awesome\nAn awesome project.\n"
    assert (project / "LICENSE").is_file()


def test_update_conflict(runcutty: RunCutty, repository: Path, project: Path) -> None:
    """It exits with a non-zero status on merge conflicts."""
    updatefile(
        project / "README.md",
        """
        # awesome
        An awesome project.
        """,
    )

    updatefile(
        repository / "{{ cookiecutter.project }}" / "README.md",
        """
        # {{ cookiecutter.project }}
        An excellent project.
        """,
    )

    with chdir(project):
        with pytest.raises(Exception):
            runcutty("update")


def test_update_remove(runcutty: RunCutty, repository: Path, project: Path) -> None:
    """It applies file deletions from the template."""
    removefile(
        repository / "{{ cookiecutter.project }}" / "README.md",
    )

    with chdir(project):
        runcutty("update")

    assert not (project / "README.md").is_file()


def test_update_noop(runcutty: RunCutty, repository: Path, project: Path) -> None:
    """It does nothing if the generated project did not change."""
    oldhead = pygit2.Repository(project).head.target

    with chdir(project):
        runcutty("update")

    assert oldhead == pygit2.Repository(project).head.target


def test_update_new_variables(
    runcutty: RunCutty, repository: Path, project: Path
) -> None:
    """It prompts for variables added after the last project generation."""
    addprojectvariable(repository, "status", ["alpha", "beta", "stable"])

    with chdir(project):
        runcutty("update", input="3\n")

    assert "stable" == projectvariable(project, "status")


def test_update_extra_context_old_variable(
    runcutty: RunCutty, repository: Path, project: Path
) -> None:
    """It allows setting variables on the command-line."""
    with chdir(project):
        runcutty("update", "project=excellent")

    assert "excellent" == projectvariable(project, "project")


def test_update_extra_context_new_variable(
    runcutty: RunCutty, repository: Path, project: Path
) -> None:
    """It allows setting variables on the command-line."""
    addprojectvariable(repository, "status", ["alpha", "beta", "stable"])

    with chdir(project):
        runcutty("update", "status=stable")

    assert "stable" == projectvariable(project, "status")


def test_update_no_input(runcutty: RunCutty, repository: Path, project: Path) -> None:
    """It does not prompt for variables added after the last project generation."""
    addprojectvariable(repository, "status", ["alpha", "beta", "stable"])

    with chdir(project):
        runcutty("update", "--no-input", input="3\n")

    assert "alpha" == projectvariable(project, "status")


def test_update_rename_projectdir(
    runcutty: RunCutty, repository: Path, project: Path
) -> None:
    """It generates the project in the project directory irrespective of its name."""
    project2 = Path("awesome2")
    project.rename(project2)

    updatefile(
        repository / "{{ cookiecutter.project }}" / "README.md",
        """
        # {{ cookiecutter.project }}
        An awesome project.
        """,
    )

    with chdir(project2):
        runcutty("update")

    # Verify that the README was updated.
    assert (project2 / "README.md").read_text() == "# awesome\nAn awesome project.\n"


def test_update_cwd(runcutty: RunCutty, repository: Path, project: Path) -> None:
    """It updates the project in the specified directory."""
    updatefile(
        repository / "{{ cookiecutter.project }}" / "README.md",
        """
        # {{ cookiecutter.project }}
        An awesome project.
        """,
    )

    runcutty("update", f"--cwd={project}")

    assert (project / "README.md").read_text() == "# awesome\nAn awesome project.\n"
