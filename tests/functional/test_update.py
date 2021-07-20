"""Functional tests for the update CLI."""
import json
import os
from pathlib import Path

import pygit2
import pytest

from tests.functional.conftest import RunCutty
from tests.util.git import removefile
from tests.util.git import updatefile


def test_help(runcutty: RunCutty) -> None:
    """It exits with a status code of zero."""
    runcutty("update", "--help")


def test_update_trivial(runcutty: RunCutty, repository: Path) -> None:
    """It applies changes from the template."""
    runcutty("create", "--no-input", str(repository), "project=awesome")

    updatefile(
        repository / "{{ cookiecutter.project }}" / "README.md",
        """
        # {{ cookiecutter.project }}
        An awesome project.
        """,
    )

    # Update the project.
    os.chdir("awesome")
    runcutty("update")

    assert Path("README.md").read_text() == "# awesome\nAn awesome project.\n"


def test_update_merge(runcutty: RunCutty, repository: Path) -> None:
    """It merges changes from the template."""
    runcutty("create", "--no-input", str(repository), "project=awesome")

    projectdir = Path("awesome")

    updatefile(
        projectdir / "README.md",
        """
        # awesome
        An awesome project.
        """,
    )

    updatefile(
        repository / "{{ cookiecutter.project }}" / "LICENSE",
        "",
    )

    # Update the project.
    os.chdir(projectdir)
    runcutty("update")

    assert Path("README.md").read_text() == "# awesome\nAn awesome project.\n"
    assert Path("LICENSE").is_file()


def test_update_conflict(runcutty: RunCutty, repository: Path) -> None:
    """It exits with a non-zero status on merge conflicts."""
    runcutty("create", "--no-input", str(repository), "project=awesome")

    projectdir = Path("awesome")

    updatefile(
        projectdir / "README.md",
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

    # Update the project.
    os.chdir(projectdir)
    with pytest.raises(Exception):
        runcutty("update")


def test_update_remove(runcutty: RunCutty, repository: Path) -> None:
    """It applies file deletions from the template."""
    runcutty("create", "--no-input", str(repository), "project=awesome")

    projectdir = Path("awesome")

    removefile(
        repository / "{{ cookiecutter.project }}" / "README.md",
    )

    # Update the project.
    os.chdir(projectdir)
    runcutty("update")

    assert not Path("README.md").is_file()


def test_update_noop(runcutty: RunCutty, repository: Path) -> None:
    """It does nothing if the generated project did not change."""
    runcutty("create", "--no-input", str(repository), "project=awesome")

    projectdir = Path("awesome")
    project = pygit2.Repository(projectdir)
    oldhead = project.head.target

    os.chdir(projectdir)
    runcutty("update")

    assert oldhead == project.head.target


def test_update_new_variables(runcutty: RunCutty, repository: Path) -> None:
    """It prompts for variables added after the last project generation."""
    runcutty("create", "--no-input", str(repository), "project=awesome")

    # Add project variable `status`.
    path = repository / "cookiecutter.json"
    data = json.loads(path.read_text())
    data["status"] = ["alpha", "beta", "stable"]
    updatefile(path, json.dumps(data))

    # Update the project.
    os.chdir("awesome")
    runcutty("update", input="3\n")

    # Verify that the variable was bound by user input.
    path = Path(".cookiecutter.json")
    data = json.loads(path.read_text())
    assert "stable" == data["status"]


def test_update_extra_context_old_variable(
    runcutty: RunCutty, repository: Path
) -> None:
    """It allows setting variables on the command-line."""
    runcutty("create", "--no-input", str(repository), "project=awesome")

    # Update the project.
    os.chdir("awesome")
    runcutty("update", "project=excellent")

    # Verify that the variable was bound.
    path = Path(".cookiecutter.json")
    data = json.loads(path.read_text())
    assert "excellent" == data["project"]


def test_update_extra_context_new_variable(
    runcutty: RunCutty, repository: Path
) -> None:
    """It allows setting variables on the command-line."""
    runcutty("create", "--no-input", str(repository), "project=awesome")

    # Add project variable `status`.
    path = repository / "cookiecutter.json"
    data = json.loads(path.read_text())
    data["status"] = ["alpha", "beta", "stable"]
    updatefile(path, json.dumps(data))

    # Update the project.
    os.chdir("awesome")
    runcutty("update", "status=stable")

    # Verify that the variable was bound.
    path = Path(".cookiecutter.json")
    data = json.loads(path.read_text())
    assert "stable" == data["status"]


def test_update_no_input(runcutty: RunCutty, repository: Path) -> None:
    """It does not prompt for variables added after the last project generation."""
    runcutty("create", "--no-input", str(repository), "project=awesome")

    # Add project variable `status`.
    path = repository / "cookiecutter.json"
    data = json.loads(path.read_text())
    data["status"] = ["alpha", "beta", "stable"]
    updatefile(path, json.dumps(data))

    # Update the project.
    os.chdir("awesome")
    runcutty("update", "--no-input", input="3\n")

    # Verify that the variable was bound using the default.
    path = Path(".cookiecutter.json")
    data = json.loads(path.read_text())
    assert "alpha" == data["status"]


def test_update_rename_projectdir(runcutty: RunCutty, repository: Path) -> None:
    """It generates the project in the project directory irrespective of its name."""
    runcutty("create", "--no-input", str(repository), "project=awesome")

    # Rename the project directory.
    projectdir = Path("awesome")
    projectdir.rename("awesome2")

    updatefile(
        repository / "{{ cookiecutter.project }}" / "README.md",
        """
        # {{ cookiecutter.project }}
        An awesome project.
        """,
    )

    # Update the project.
    os.chdir("awesome2")
    runcutty("update")

    # Verify that the README was updated.
    assert Path("README.md").read_text() == "# awesome\nAn awesome project.\n"


def test_update_cwd(runcutty: RunCutty, repository: Path) -> None:
    """It updates the project in the specified directory."""
    runcutty("create", "--no-input", str(repository), "project=awesome")

    updatefile(
        repository / "{{ cookiecutter.project }}" / "README.md",
        """
        # {{ cookiecutter.project }}
        An awesome project.
        """,
    )

    # Update the project.
    projectdir = Path("awesome")
    runcutty("update", f"--cwd={projectdir}")

    assert (projectdir / "README.md").read_text() == "# awesome\nAn awesome project.\n"
