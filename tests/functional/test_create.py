"""Functional tests for the create CLI."""
from pathlib import Path

import pytest

from cutty.templates.adapters.cookiecutter.projectconfig import PROJECT_CONFIG_FILE
from tests.functional.conftest import RunCutty
from tests.util.files import project_files
from tests.util.files import template_files
from tests.util.git import move_repository_files_to_subdirectory
from tests.util.git import updatefile


EXTRA = {Path("post_gen_project"), Path(PROJECT_CONFIG_FILE)}


def test_help(runcutty: RunCutty) -> None:
    """It exits with a status code of zero."""
    runcutty("create", "--help")


def test_input(runcutty: RunCutty, template: Path) -> None:
    """It binds project variables from user input."""
    runcutty("create", str(template), input="foobar\n\n\n")

    assert Path("foobar", "README.md").read_text() == "# foobar\n"


def test_hook(runcutty: RunCutty, template: Path) -> None:
    """It runs hooks."""
    runcutty("create", str(template))

    assert Path("example", "post_gen_project").is_file()


def test_files(runcutty: RunCutty, template: Path) -> None:
    """It renders the project files."""
    runcutty("create", str(template))

    assert template_files(template) == project_files("example") - EXTRA


def test_cutty_json(runcutty: RunCutty, template: Path) -> None:
    """It creates a cutty.json file."""
    runcutty("create", str(template))

    assert Path("example", PROJECT_CONFIG_FILE).is_file()


def test_cutty_json_already_exists(runcutty: RunCutty, template: Path) -> None:
    """It raises an exception."""
    updatefile(template / "{{ cookiecutter.project }}" / PROJECT_CONFIG_FILE)

    with pytest.raises(FileExistsError):
        runcutty("create", str(template))


def test_inplace(runcutty: RunCutty, template: Path) -> None:
    """It generates the project files in the current directory."""
    runcutty("create", "--no-input", "--in-place", str(template))

    assert template_files(template) == project_files(".") - EXTRA


def test_directory(runcutty: RunCutty, template: Path, tmp_path: Path) -> None:
    """It uses the template in the given subdirectory."""
    directory = "a"
    move_repository_files_to_subdirectory(template, directory)

    runcutty("create", f"--directory={directory}", str(template))

    assert template_files(template / "a") == project_files("example") - EXTRA
