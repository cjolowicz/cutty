"""Functional tests for the create CLI."""
from pathlib import Path

import pytest

from tests.functional.conftest import RunCutty
from tests.util.files import project_files
from tests.util.files import template_files
from tests.util.git import move_repository_files_to_subdirectory
from tests.util.git import removefile


def test_help(runcutty: RunCutty) -> None:
    """It exits with a status code of zero."""
    runcutty("create", "--help")


def test_input(runcutty: RunCutty, repository: Path) -> None:
    """It binds project variables from user input."""
    runcutty("create", str(repository), input="foobar\n\n\n")

    assert Path("foobar", "README.md").read_text() == "# foobar\n"


def test_hook(runcutty: RunCutty, repository: Path) -> None:
    """It runs hooks."""
    runcutty("create", str(repository))

    assert Path("example", "post_gen_project").is_file()


def test_files(runcutty: RunCutty, repository: Path) -> None:
    """It renders the project files."""
    runcutty("create", str(repository))

    assert template_files(repository) == project_files("example") - {
        Path("post_gen_project")
    }


@pytest.mark.xfail(reason="TODO")
def test_cookiecutter_json(runcutty: RunCutty, repository: Path) -> None:
    """It always creates .cookiecutter.json."""
    removefile(repository / "{{ cookiecutter.project }}" / ".cookiecutter.json")

    runcutty("create", str(repository))

    assert Path("example", ".cookiecutter.json").is_file()


def test_create_inplace(runcutty: RunCutty, repository: Path) -> None:
    """It generates the project files in the current directory."""
    runcutty("create", "--no-input", "--in-place", str(repository))

    assert Path("README.md").read_text() == "# example\n"
    assert Path("post_gen_project").is_file()
    assert Path(".cookiecutter.json").is_file()


def test_directory(runcutty: RunCutty, repository: Path, tmp_path: Path) -> None:
    """It uses the template in the given subdirectory."""
    directory = "a"
    move_repository_files_to_subdirectory(repository, directory)

    runcutty("create", f"--directory={directory}", str(repository))

    assert template_files(repository / "a") == project_files("example") - {
        Path("post_gen_project")
    }
