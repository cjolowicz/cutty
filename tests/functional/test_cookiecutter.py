"""Functional tests for the cookiecutter CLI."""
from pathlib import Path

import pygit2

from tests.functional.conftest import RunCutty
from tests.util.files import project_files
from tests.util.files import template_files
from tests.util.git import move_repository_files_to_subdirectory
from tests.util.git import removefile
from tests.util.git import updatefile


EXTRA = Path("post_gen_project")


def test_create_help(runcutty: RunCutty) -> None:
    """It exits with a status code of zero."""
    runcutty("cookiecutter", "--help")


def test_create_cookiecutter(runcutty: RunCutty, repository: Path) -> None:
    """It generates a project."""
    runcutty("cookiecutter", str(repository), input="foobar\n\n\n")

    assert Path("foobar", "README.md").read_text() == "# foobar\n"
    assert Path("foobar", "post_gen_project").is_file()
    assert Path("foobar", ".cookiecutter.json").is_file()


def test_no_repository(runcutty: RunCutty, repository: Path) -> None:
    """It does not create a git repository for the project."""
    runcutty("cookiecutter", str(repository))

    assert not Path("example", ".git").is_dir()


def test_no_cookiecutter_json(runcutty: RunCutty, repository: Path) -> None:
    """It does not create .cookiecutter.json unless the template provides it."""
    removefile(repository / "{{ cookiecutter.project }}" / ".cookiecutter.json")

    runcutty("cookiecutter", str(repository))

    assert not Path("example", ".cookiecutter.json").is_file()


def test_no_input(runcutty: RunCutty, repository: Path) -> None:
    """It does not prompt for variables."""
    runcutty("cookiecutter", "--no-input", str(repository))

    assert template_files(repository) == project_files("example") - {EXTRA}


def test_extra_context(runcutty: RunCutty, repository: Path) -> None:
    """It allows setting variables on the command-line."""
    runcutty("cookiecutter", str(repository), "project=awesome")

    assert template_files(repository) == project_files("awesome") - {EXTRA}


def test_checkout(runcutty: RunCutty, repository: Path) -> None:
    """It uses the specified revision of the template."""
    initial = pygit2.Repository(repository).head.target

    updatefile(
        repository / "{{ cookiecutter.project }}" / "LICENSE",
        "",
    )

    runcutty("cookiecutter", f"--checkout={initial}", str(repository))

    assert not Path("example", "LICENSE").exists()


def test_output_dir(runcutty: RunCutty, repository: Path, tmp_path: Path) -> None:
    """It generates the project under the specified directory."""
    outputdir = tmp_path / "outputdir"

    runcutty("cookiecutter", f"--output-dir={outputdir}", str(repository))

    assert template_files(repository) == project_files(outputdir / "example") - {EXTRA}


def test_directory(runcutty: RunCutty, repository: Path, tmp_path: Path) -> None:
    """It uses the template in the given subdirectory."""
    directory = "a"
    move_repository_files_to_subdirectory(repository, directory)

    runcutty("cookiecutter", f"--directory={directory}", str(repository))

    assert template_files(repository / "a") == project_files("example") - {EXTRA}


def test_overwrite(runcutty: RunCutty, repository: Path) -> None:
    """It overwrites existing files."""
    readme = Path("example", "README.md")
    readme.parent.mkdir()
    readme.touch()

    runcutty("cookiecutter", "--overwrite-if-exists", str(repository))

    assert readme.read_text() == "# example\n"


def test_skip(runcutty: RunCutty, repository: Path) -> None:
    """It skips existing files."""
    readme = Path("example", "README.md")
    readme.parent.mkdir()
    readme.touch()

    runcutty(
        "cookiecutter",
        "--overwrite-if-exists",
        "--skip-if-file-exists",
        str(repository),
    )

    assert readme.read_text() == ""
