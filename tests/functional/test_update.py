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


def updateprojectvariable(repository: Path, name: str, value: Any) -> None:
    """Add or update a project variable in the template."""
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
    updateprojectvariable(repository, "status", ["alpha", "beta", "stable"])

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
    updateprojectvariable(repository, "status", ["alpha", "beta", "stable"])

    with chdir(project):
        runcutty("update", "status=stable")

    assert "stable" == projectvariable(project, "status")


def test_update_no_input(runcutty: RunCutty, repository: Path, project: Path) -> None:
    """It does not prompt for variables added after the last project generation."""
    updateprojectvariable(repository, "status", ["alpha", "beta", "stable"])

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


def test_update_dictvariable(runcutty: RunCutty, repository: Path) -> None:
    """It loads dict variables from the project configuration."""
    # Add a dict variable with image types to the template.
    images = {
        "png": {
            "name": "Portable Network Graphic",
            "library": "libpng",
            "apps": ["GIMP"],
        },
        "bmp": {
            "name": "Bitmap",
            "library": "libbmp",
            "apps": ["Paint", "GIMP"],
        },
    }

    updateprojectvariable(repository, "images", images)

    # Create a project using only PNG images.
    pngimages = {key: value for key, value in images.items() if key == "png"}
    userinput = "\n".join(
        [
            "",  # project
            "",  # license
            "",  # cli
            json.dumps(pngimages),
        ]
    )

    runcutty("create", str(repository), input=userinput)

    # Add LICENSE so update has something to do.
    updatefile(
        repository / "{{ cookiecutter.project }}" / "LICENSE",
        "",
    )

    # Update the project.
    project = Path("example")

    runcutty("update", f"--cwd={project}")

    assert pngimages == projectvariable(project, "images")


def test_update_private_variables(
    runcutty: RunCutty, repository: Path, project: Path
) -> None:
    """It does not bind private variables from the project configuration."""
    # Add another Jinja extension to `_extensions`.
    extensions: list[str] = projectvariable(project, "_extensions")
    extensions.append("jinja2.ext.i18n")
    updateprojectvariable(repository, "_extensions", extensions)

    runcutty("update", f"--cwd={project}")

    assert extensions == projectvariable(project, "_extensions")
