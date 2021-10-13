"""Functional tests for the update CLI."""
import json
from pathlib import Path
from typing import Any

import pygit2
import pytest

from cutty.projects.projectconfig import readprojectconfigfile
from cutty.util.git import Repository
from tests.functional.conftest import RunCutty
from tests.functional.conftest import RunCuttyError
from tests.util.files import chdir
from tests.util.git import appendfile
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

    runcutty("create", "--non-interactive", str(template), f"project={project.name}")

    return project


def templatevariable(template: Path, name: str) -> Any:
    """Return the value of a template variable."""
    path = template / "cookiecutter.json"
    data = json.loads(path.read_text())
    return data[name]


def updatetemplatevariable(template: Path, name: str, value: Any) -> None:
    """Add or update a template variable."""
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
    appendfile(templateproject / "README.md", "An awesome project.\n")

    with chdir(project):
        runcutty("update")

    assert (project / "README.md").read_text() == "# awesome\nAn awesome project.\n"


def test_merge(runcutty: RunCutty, templateproject: Path, project: Path) -> None:
    """It merges changes from the template."""
    appendfile(project / "README.md", "An awesome project.\n")
    updatefile(templateproject / "LICENSE")

    with chdir(project):
        runcutty("update")

    assert (project / "README.md").read_text() == "# awesome\nAn awesome project.\n"
    assert (project / "LICENSE").is_file()


def test_conflict(runcutty: RunCutty, templateproject: Path, project: Path) -> None:
    """It exits with a non-zero status on merge conflicts."""
    appendfile(project / "README.md", "An awesome project.\n")
    appendfile(templateproject / "README.md", "An excellent project.\n")

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
    repository = Repository.open(project)
    oldhead = repository.head.commit

    with chdir(project):
        runcutty("update")

    assert oldhead == repository.head.commit


def test_new_variables(runcutty: RunCutty, template: Path, project: Path) -> None:
    """It prompts for variables added after the last project generation."""
    updatetemplatevariable(template, "status", ["alpha", "beta", "stable"])

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
    updatetemplatevariable(template, "status", ["alpha", "beta", "stable"])

    with chdir(project):
        runcutty("update", "status=stable")

    assert "stable" == projectvariable(project, "status")


def test_non_interactive(runcutty: RunCutty, template: Path, project: Path) -> None:
    """It does not prompt for variables added after the last project generation."""
    updatetemplatevariable(template, "status", ["alpha", "beta", "stable"])

    with chdir(project):
        runcutty("update", "--non-interactive", input="3\n")

    assert "alpha" == projectvariable(project, "status")


def test_rename_projectdir(
    runcutty: RunCutty, templateproject: Path, project: Path
) -> None:
    """It generates the project in the project directory irrespective of its name."""
    project2 = Path("awesome2")
    project.rename(project2)

    appendfile(templateproject / "README.md", "An awesome project.\n")

    with chdir(project2):
        runcutty("update")

    assert (project2 / "README.md").read_text() == "# awesome\nAn awesome project.\n"


def test_cwd(runcutty: RunCutty, templateproject: Path, project: Path) -> None:
    """It updates the project in the specified directory."""
    appendfile(templateproject / "README.md", "An awesome project.\n")

    runcutty("update", f"--cwd={project}")

    assert (project / "README.md").read_text() == "# awesome\nAn awesome project.\n"


def test_dictvariable(
    runcutty: RunCutty, template: Path, templateproject: Path
) -> None:
    """It loads dict variables from the project configuration."""
    updatetemplatevariable(
        template,
        "images",
        {
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
        },
    )

    def pngimages(template: Path) -> Any:
        """Filter the `images` dict variable to contain only PNG."""
        images = templatevariable(template, "images")
        return {key: value for key, value in images.items() if key == "png"}

    runcutty(
        "create",
        str(template),
        input="\n".join(
            [
                "",  # project
                "",  # license
                "",  # cli
                json.dumps(pngimages(template)),
            ]
        ),
    )

    updatefile(templateproject / "LICENSE")

    project = Path("example")

    runcutty("update", f"--cwd={project}")

    assert pngimages(template) == projectvariable(project, "images")


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
    updatetemplatevariable(template, "_extensions", extensions)

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


def test_revision(
    runcutty: RunCutty, template: Path, templateproject: Path, project: Path
) -> None:
    """It uses the specified revision of the template."""
    updatefile(templateproject / "LICENSE", "a")

    revision = Repository.open(template).head.commit.id

    updatefile(templateproject / "LICENSE", "b")

    runcutty("update", f"--cwd={project}", f"--revision={revision}")

    assert (project / "LICENSE").read_text() == "a"


def test_abort(runcutty: RunCutty, templateproject: Path, project: Path) -> None:
    """It does not skip changes when a previous update was aborted."""
    updatefile(project / "LICENSE", "a")
    updatefile(templateproject / "LICENSE", "b")

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
    updatefile(project / "LICENSE", "a")
    updatefile(templateproject / "LICENSE", "b")

    with pytest.raises(Exception, match="conflict"):
        runcutty("update", f"--cwd={project}")

    resolveconflicts(project, project / "LICENSE", Side.THEIRS)

    runcutty("update", f"--cwd={project}", "--continue")

    assert (project / "LICENSE").read_text() == "b"


def test_skip(runcutty: RunCutty, templateproject: Path, project: Path) -> None:
    """It skips the update."""
    updatefile(project / "LICENSE", "a")
    updatefile(templateproject / "LICENSE", "b")

    with pytest.raises(Exception, match="conflict"):
        runcutty("update", f"--cwd={project}")

    runcutty("update", f"--cwd={project}", "--skip")

    updatefile(templateproject / "INSTALL")

    runcutty("update", f"--cwd={project}")

    assert (project / "LICENSE").read_text() == "a"
    assert (project / "INSTALL").is_file()


def test_skip_without_update(runcutty: RunCutty, project: Path) -> None:
    """It exits with a non-zero status code."""
    with pytest.raises(RunCuttyError):
        runcutty("update", f"--cwd={project}", "--skip")


def test_empty_template(emptytemplate: Path, runcutty: RunCutty) -> None:
    """It exits with a non-zero status code."""
    (emptytemplate / "{{ cookiecutter.project }}" / "marker").touch()

    runcutty("create", str(emptytemplate))

    (emptytemplate / "{{ cookiecutter.project }}" / "marker").unlink()

    with pytest.raises(RunCuttyError):
        runcutty("update", "--cwd=project")


def undo(repository: Repository) -> None:
    """Hard-reset to the parent of HEAD."""
    [parent] = repository.head.commit.parents
    repository._repository.reset(parent.id, pygit2.GIT_RESET_HARD)


def test_reverted_update(
    runcutty: RunCutty, templateproject: Path, project: Path
) -> None:
    """It does not skip changes when a previous update was reverted."""
    # Update #1: Add file 'a'
    updatefile(templateproject / "a")
    runcutty("update", f"--cwd={project}")

    # Update #2: Add file 'b'
    updatefile(templateproject / "b")
    runcutty("update", f"--cwd={project}")

    # "Revert" project updates (hard reset).
    repository = Repository.open(project)
    undo(repository)
    undo(repository)

    # Update #3: Add files 'a' and 'b'
    runcutty("update", f"--cwd={project}")

    assert "a" in repository.head.commit.tree
    assert "b" in repository.head.commit.tree


def test_no_branches(runcutty: RunCutty, templateproject: Path, project: Path) -> None:
    """It does not create additional branches."""
    repository = Repository.open(project)
    branches = list(repository.heads)

    updatefile(templateproject / "LICENSE")
    runcutty("update", f"--cwd={project}")

    assert branches == list(repository.heads)
