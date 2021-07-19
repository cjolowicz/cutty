"""Functional tests for the create CLI."""
from pathlib import Path

from tests.functional.conftest import RunCutty
from tests.util.git import move_repository_files_to_subdirectory


def test_create_help(runcutty: RunCutty) -> None:
    """It exits with a status code of zero."""
    runcutty("create", "--help")


def test_create_cookiecutter(runcutty: RunCutty, repository: Path) -> None:
    """It generates a project."""
    runcutty("create", str(repository), input="foobar\n\n\n")

    assert Path("foobar", "README.md").read_text() == "# foobar\n"
    assert Path("foobar", "post_gen_project").is_file()
    assert Path("foobar", ".cookiecutter.json").is_file()


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

    assert Path("example", "README.md").is_file()
