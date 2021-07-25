"""Functional tests for the update CLI."""
import json
from pathlib import Path
from typing import Any

import pygit2
import pytest

from cutty.templates.adapters.cookiecutter.projectconfig import readprojectconfigfile
from tests.functional.conftest import RunCutty
from tests.util.files import chdir
from tests.util.git import move_repository_files_to_subdirectory
from tests.util.git import removefile
from tests.util.git import updatefile


def test_help(runcutty: RunCutty) -> None:
    """It exits with a status code of zero."""
    runcutty("update", "--help")


@pytest.fixture
def project(runcutty: RunCutty, template: Path) -> Path:
    """Fixture for a generated project."""
    project = Path("awesome")

    runcutty("create", "--no-input", str(template), f"project={project.name}")

    return project


def updateprojectvariable(template: Path, name: str, value: Any) -> None:
    """Add or update a project variable in the template."""
    path = template / "cookiecutter.json"
    data = json.loads(path.read_text())
    data[name] = value
    updatefile(path, json.dumps(data))


def projectvariable(project: Path, name: str) -> Any:
    """Return the bound value of a project variable."""
    config = readprojectconfigfile(project)
    return next(binding.value for binding in config.bindings if binding.name == name)


def test_trivial(runcutty: RunCutty, template: Path, project: Path) -> None:
    """It applies changes from the template."""
    updatefile(
        template / "{{ cookiecutter.project }}" / "README.md",
        """
        # {{ cookiecutter.project }}
        An awesome project.
        """,
    )

    with chdir(project):
        runcutty("update")

    assert (project / "README.md").read_text() == "# awesome\nAn awesome project.\n"


def test_merge(runcutty: RunCutty, template: Path, project: Path) -> None:
    """It merges changes from the template."""
    updatefile(
        project / "README.md",
        """
        # awesome
        An awesome project.
        """,
    )

    updatefile(template / "{{ cookiecutter.project }}" / "LICENSE")

    with chdir(project):
        runcutty("update")

    assert (project / "README.md").read_text() == "# awesome\nAn awesome project.\n"
    assert (project / "LICENSE").is_file()


def test_conflict(runcutty: RunCutty, template: Path, project: Path) -> None:
    """It exits with a non-zero status on merge conflicts."""
    updatefile(
        project / "README.md",
        """
        # awesome
        An awesome project.
        """,
    )

    updatefile(
        template / "{{ cookiecutter.project }}" / "README.md",
        """
        # {{ cookiecutter.project }}
        An excellent project.
        """,
    )

    with chdir(project):
        with pytest.raises(Exception):
            runcutty("update")


def test_remove(runcutty: RunCutty, template: Path, project: Path) -> None:
    """It applies file deletions from the template."""
    removefile(template / "{{ cookiecutter.project }}" / "README.md")
    updatefile(template / "{{ cookiecutter.project }}" / ".keep")

    with chdir(project):
        runcutty("update")

    assert not (project / "README.md").is_file()


def test_noop(runcutty: RunCutty, template: Path, project: Path) -> None:
    """It does nothing if the generated project did not change."""
    oldhead = pygit2.Repository(project).head.target

    with chdir(project):
        runcutty("update")

    assert oldhead == pygit2.Repository(project).head.target


def test_new_variables(runcutty: RunCutty, template: Path, project: Path) -> None:
    """It prompts for variables added after the last project generation."""
    updateprojectvariable(template, "status", ["alpha", "beta", "stable"])

    with chdir(project):
        runcutty("update", input="3\n")

    assert "stable" == projectvariable(project, "status")


def test_extra_context_old_variable(
    runcutty: RunCutty, template: Path, project: Path
) -> None:
    """It allows setting variables on the command-line."""
    with chdir(project):
        runcutty("update", "project=excellent")

    assert "excellent" == projectvariable(project, "project")


def test_extra_context_new_variable(
    runcutty: RunCutty, template: Path, project: Path
) -> None:
    """It allows setting variables on the command-line."""
    updateprojectvariable(template, "status", ["alpha", "beta", "stable"])

    with chdir(project):
        runcutty("update", "status=stable")

    assert "stable" == projectvariable(project, "status")


def test_no_input(runcutty: RunCutty, template: Path, project: Path) -> None:
    """It does not prompt for variables added after the last project generation."""
    updateprojectvariable(template, "status", ["alpha", "beta", "stable"])

    with chdir(project):
        runcutty("update", "--no-input", input="3\n")

    assert "alpha" == projectvariable(project, "status")


def test_rename_projectdir(runcutty: RunCutty, template: Path, project: Path) -> None:
    """It generates the project in the project directory irrespective of its name."""
    project2 = Path("awesome2")
    project.rename(project2)

    updatefile(
        template / "{{ cookiecutter.project }}" / "README.md",
        """
        # {{ cookiecutter.project }}
        An awesome project.
        """,
    )

    with chdir(project2):
        runcutty("update")

    assert (project2 / "README.md").read_text() == "# awesome\nAn awesome project.\n"


def test_cwd(runcutty: RunCutty, template: Path, project: Path) -> None:
    """It updates the project in the specified directory."""
    updatefile(
        template / "{{ cookiecutter.project }}" / "README.md",
        """
        # {{ cookiecutter.project }}
        An awesome project.
        """,
    )

    runcutty("update", f"--cwd={project}")

    assert (project / "README.md").read_text() == "# awesome\nAn awesome project.\n"


def test_dictvariable(runcutty: RunCutty, template: Path) -> None:
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

    updateprojectvariable(template, "images", images)

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

    runcutty("create", str(template), input=userinput)

    # Add LICENSE so update has something to do.
    updatefile(template / "{{ cookiecutter.project }}" / "LICENSE")

    # Update the project.
    project = Path("example")

    runcutty("update", f"--cwd={project}")

    assert pngimages == projectvariable(project, "images")


def test_private_variables(runcutty: RunCutty, template: Path) -> None:
    """It does not bind private variables from the project configuration."""

    def adddotcookiecutterjson(template: Path) -> None:
        """Add .cookiecutter.json file to the template."""
        path = template / "{{ cookiecutter.project }}" / ".cookiecutter.json"
        text = "{{ cookiecutter | jsonify }}"
        updatefile(path, text)

    def privatevariable(project: Path, variable: str) -> Any:
        """Return any variable from the Cookiecutter context of a generated project."""
        context = json.loads((project / ".cookiecutter.json").read_text())
        return context[variable]

    adddotcookiecutterjson(template)

    project = Path("example")

    runcutty("create", str(template))

    # Add another Jinja extension to `_extensions`.
    extensions: list[str] = privatevariable(project, "_extensions")
    extensions.append("jinja2.ext.i18n")
    updateprojectvariable(template, "_extensions", extensions)

    runcutty("update", f"--cwd={project}")

    assert extensions == privatevariable(project, "_extensions")


def test_directory_projectconfig(runcutty: RunCutty, template: Path) -> None:
    """It uses the template directory specified in the project configuration."""
    project = Path("example")
    directory = "a"
    move_repository_files_to_subdirectory(template, directory)

    runcutty("create", f"--directory={directory}", str(template))
    updatefile(template / "a" / "{{ cookiecutter.project }}" / "LICENSE")
    runcutty("update", f"--cwd={project}")

    assert (project / "LICENSE").is_file()


def test_directory_update(runcutty: RunCutty, template: Path, project: Path) -> None:
    """It uses the template directory specified when updating."""
    directory = "a"
    move_repository_files_to_subdirectory(template, directory)

    runcutty("update", f"--cwd={project}", f"--directory={directory}")

    config = readprojectconfigfile(project)
    assert directory == str(config.directory)


def test_checkout(runcutty: RunCutty, template: Path, project: Path) -> None:
    """It uses the specified revision of the template."""
    updatefile(template / "{{ cookiecutter.project }}" / "LICENSE", "first version")

    revision = pygit2.Repository(template).head.target

    updatefile(template / "{{ cookiecutter.project }}" / "LICENSE", "second version")

    runcutty("update", f"--cwd={project}", f"--checkout={revision}")

    assert (project / "LICENSE").read_text() == "first version"


@pytest.mark.xfail(reason="TODO")
def test_conflict_abort(runcutty: RunCutty, template: Path, project: Path) -> None:
    """It does not skip changes when a previous update was aborted."""
    updatefile(project / "LICENSE", "this is the version in the project")
    updatefile(
        template / "{{ cookiecutter.project }}" / "LICENSE",
        "this is the version in the template",
    )

    with pytest.raises(Exception, match="conflict"):
        runcutty("update", f"--cwd={project}")

    # Abort the cherry-pick, unceremoniously.
    repository = pygit2.Repository(project)
    repository.reset(repository.head.target, pygit2.GIT_RESET_HARD)

    # Update the template with an unproblematic change.
    updatefile(template / "{{ cookiecutter.project }}" / "INSTALL")

    # Repeat the update, it should fail again.
    with pytest.raises(Exception, match="conflict"):
        runcutty("update", f"--cwd={project}")
