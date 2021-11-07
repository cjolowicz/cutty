"""Functional tests for the cookiecutter CLI."""
from pathlib import Path

import pytest

from cutty.projects.config import PROJECT_CONFIG_FILE
from cutty.util.git import Repository
from tests.functional.conftest import RunCutty
from tests.functional.conftest import RunCuttyError
from tests.util.files import project_files
from tests.util.files import template_files
from tests.util.git import move_repository_files_to_subdirectory
from tests.util.git import updatefile
from tests.util.keys import BACKSPACE
from tests.util.keys import RETURN


EXTRA = Path("post_gen_project")


def test_help(runcutty: RunCutty) -> None:
    """It exits with a status code of zero."""
    runcutty("cookiecutter", "--help")


def test_default(runcutty: RunCutty, template: Path) -> None:
    """It generates a project."""
    runcutty("cookiecutter", str(template), input=RETURN * 3)

    assert template_files(template) == project_files("example") - {EXTRA}


def test_input(runcutty: RunCutty, template: Path) -> None:
    """It generates a project."""
    runcutty(
        "cookiecutter",
        str(template),
        input=BACKSPACE * len("example") + "foobar" + RETURN * 3,
    )

    assert Path("foobar", "README.md").read_text() == "# foobar\n"


def test_no_input(runcutty: RunCutty, template: Path) -> None:
    """It does not prompt for variables."""
    runcutty("cookiecutter", "--no-input", str(template))

    assert template_files(template) == project_files("example") - {EXTRA}


def test_no_repository(runcutty: RunCutty, template: Path) -> None:
    """It does not create a git repository for the project."""
    runcutty("cookiecutter", "--no-input", str(template))

    assert not Path("example", ".git").is_dir()


def test_no_cutty_json(runcutty: RunCutty, template: Path) -> None:
    """It does not create a cutty.json file."""
    runcutty("cookiecutter", "--no-input", str(template))

    assert not Path("example", PROJECT_CONFIG_FILE).is_file()


def test_extra_context(runcutty: RunCutty, template: Path) -> None:
    """It allows setting variables on the command-line."""
    runcutty("cookiecutter", "--no-input", str(template), "project=awesome")

    assert template_files(template) == project_files("awesome") - {EXTRA}


def test_extra_context_invalid(runcutty: RunCutty, template: Path) -> None:
    """It raises an exception if additional arguments cannot be parsed."""
    with pytest.raises(Exception):
        runcutty("cookiecutter", "--no-input", str(template), "invalid")


def test_checkout(runcutty: RunCutty, template: Path) -> None:
    """It uses the specified revision of the template."""
    initial = Repository.open(template).head.commit.id

    updatefile(template / "{{ cookiecutter.project }}" / "LICENSE")

    runcutty("cookiecutter", "--no-input", f"--checkout={initial}", str(template))

    assert not Path("example", "LICENSE").exists()


def test_output_dir(runcutty: RunCutty, template: Path, tmp_path: Path) -> None:
    """It generates the project under the specified directory."""
    outputdir = tmp_path / "outputdir"

    runcutty("cookiecutter", "--no-input", f"--output-dir={outputdir}", str(template))

    assert template_files(template) == project_files(outputdir / "example") - {EXTRA}


def test_directory(runcutty: RunCutty, template: Path, tmp_path: Path) -> None:
    """It uses the template in the given subdirectory."""
    directory = "a"
    move_repository_files_to_subdirectory(template, directory)

    runcutty("cookiecutter", "--no-input", f"--directory={directory}", str(template))

    assert template_files(template / "a") == project_files("example") - {EXTRA}


def test_overwrite(runcutty: RunCutty, template: Path) -> None:
    """It overwrites existing files."""
    readme = Path("example", "README.md")
    readme.parent.mkdir()
    readme.touch()

    runcutty("cookiecutter", "--no-input", "--overwrite-if-exists", str(template))

    assert readme.read_text() == "# example\n"


def test_skip(runcutty: RunCutty, template: Path) -> None:
    """It skips existing files."""
    readme = Path("example", "README.md")
    readme.parent.mkdir()
    readme.touch()

    runcutty(
        "cookiecutter",
        "--no-input",
        "--overwrite-if-exists",
        "--skip-if-file-exists",
        str(template),
    )

    assert readme.read_text() == ""


def test_empty_template(emptytemplate: Path, runcutty: RunCutty) -> None:
    """It exits with a non-zero status code."""
    with pytest.raises(RunCuttyError):
        runcutty("cookiecutter", "--no-input", str(emptytemplate))
