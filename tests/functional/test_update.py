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
from tests.util.git import resolveconflicts
from tests.util.git import Side
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


@pytest.fixture
def templateproject(template: Path) -> Path:
    """Return the project directory in the template."""
    return template / "{{ cookiecutter.project }}"


def test_trivial(runcutty: RunCutty, templateproject: Path, project: Path) -> None:
    """It applies changes from the template."""
    updatefile(
        templateproject / "README.md",
        """
        # {{ cookiecutter.project }}
        An awesome project.
        """,
    )

    with chdir(project):
        runcutty("update")

    assert (project / "README.md").read_text() == "# awesome\nAn awesome project.\n"


def test_merge(runcutty: RunCutty, templateproject: Path, project: Path) -> None:
    """It merges changes from the template."""
    updatefile(
        project / "README.md",
        """
        # awesome
        An awesome project.
        """,
    )

    updatefile(templateproject / "LICENSE")

    with chdir(project):
        runcutty("update")

    assert (project / "README.md").read_text() == "# awesome\nAn awesome project.\n"
    assert (project / "LICENSE").is_file()


def test_conflict(runcutty: RunCutty, templateproject: Path, project: Path) -> None:
    """It exits with a non-zero status on merge conflicts."""
    updatefile(
        project / "README.md",
        """
        # awesome
        An awesome project.
        """,
    )

    updatefile(
        templateproject / "README.md",
        """
        # {{ cookiecutter.project }}
        An excellent project.
        """,
    )

    with chdir(project):
        with pytest.raises(Exception):
            runcutty("update")


def test_remove(runcutty: RunCutty, templateproject: Path, project: Path) -> None:
    """It applies file deletions from the template."""
    removefile(templateproject / "README.md")
    updatefile(templateproject / ".keep")

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


def test_rename_projectdir(
    runcutty: RunCutty, templateproject: Path, project: Path
) -> None:
    """It generates the project in the project directory irrespective of its name."""
    project2 = Path("awesome2")
    project.rename(project2)

    updatefile(
        templateproject / "README.md",
        """
        # {{ cookiecutter.project }}
        An awesome project.
        """,
    )

    with chdir(project2):
        runcutty("update")

    assert (project2 / "README.md").read_text() == "# awesome\nAn awesome project.\n"


def test_cwd(runcutty: RunCutty, templateproject: Path, project: Path) -> None:
    """It updates the project in the specified directory."""
    updatefile(
        templateproject / "README.md",
        """
        # {{ cookiecutter.project }}
        An awesome project.
        """,
    )

    runcutty("update", f"--cwd={project}")

    assert (project / "README.md").read_text() == "# awesome\nAn awesome project.\n"


def test_dictvariable(
    runcutty: RunCutty, template: Path, templateproject: Path
) -> None:
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
    updatefile(templateproject / "LICENSE")

    # Update the project.
    project = Path("example")

    runcutty("update", f"--cwd={project}")

    assert pngimages == projectvariable(project, "images")


def test_private_variables(
    runcutty: RunCutty, template: Path, templateproject: Path
) -> None:
    """It does not bind private variables from the project configuration."""

    def adddotcookiecutterjson(template: Path) -> None:
        """Add .cookiecutter.json file to the template."""
        path = templateproject / ".cookiecutter.json"
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


def test_checkout(
    runcutty: RunCutty, template: Path, templateproject: Path, project: Path
) -> None:
    """It uses the specified revision of the template."""
    updatefile(templateproject / "LICENSE", "first version")

    revision = pygit2.Repository(template).head.target

    updatefile(templateproject / "LICENSE", "second version")

    runcutty("update", f"--cwd={project}", f"--checkout={revision}")

    assert (project / "LICENSE").read_text() == "first version"


def test_abort(runcutty: RunCutty, templateproject: Path, project: Path) -> None:
    """It does not skip changes when a previous update was aborted."""
    updatefile(project / "LICENSE", "this is the version in the project")
    updatefile(
        templateproject / "LICENSE",
        "this is the version in the template",
    )

    with pytest.raises(Exception, match="conflict"):
        runcutty("update", f"--cwd={project}")

    # Abort the update.
    runcutty("update", f"--cwd={project}", "--abort")

    # Update the template with an unproblematic change.
    updatefile(templateproject / "INSTALL")

    # Repeat the update, it should fail again.
    with pytest.raises(Exception, match="conflict"):
        runcutty("update", f"--cwd={project}")


def test_continue(runcutty: RunCutty, templateproject: Path, project: Path) -> None:
    """It continues the update after the conflicts have been resolved."""
    updatefile(project / "LICENSE", "this is the version in the project")
    updatefile(
        templateproject / "LICENSE",
        "this is the version in the template",
    )

    with pytest.raises(Exception, match="conflict"):
        runcutty("update", f"--cwd={project}")

    resolveconflicts(project, project / "LICENSE", Side.THEIRS)

    runcutty("update", f"--cwd={project}", "--continue")

    assert (project / "LICENSE").read_text() == "this is the version in the template"


def test_skip(runcutty: RunCutty, templateproject: Path, project: Path) -> None:
    """It skips the update."""
    updatefile(project / "LICENSE", "this is the version in the project")
    updatefile(
        templateproject / "LICENSE",
        "this is the version in the template",
    )

    with pytest.raises(Exception, match="conflict"):
        runcutty("update", f"--cwd={project}")

    runcutty("update", f"--cwd={project}", "--skip")

    # Update the template with an unproblematic change.
    updatefile(templateproject / "INSTALL")

    runcutty("update", f"--cwd={project}")

    assert (project / "LICENSE").read_text() == "this is the version in the project"
    assert (project / "INSTALL").is_file()
