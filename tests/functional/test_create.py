"""Functional tests for the create CLI."""
from pathlib import Path

from click.testing import CliRunner

from cutty.entrypoints.cli import main
from tests.functional.conftest import move_repository_files_to_subdirectory


def test_create_help(runner: CliRunner) -> None:
    """It exits with a status code of zero."""
    result = runner.invoke(main, ["create", "--help"])
    assert result.exit_code == 0


def test_create_cookiecutter(runner: CliRunner, repository: Path) -> None:
    """It generates a project."""
    runner.invoke(
        main, ["create", str(repository)], input="foobar\n\n\n", catch_exceptions=False
    )
    assert Path("foobar", "README.md").read_text() == "# foobar\n"
    assert Path("foobar", "post_gen_project").is_file()
    assert Path("foobar", ".cookiecutter.json").is_file()


def test_create_inplace(runner: CliRunner, repository: Path) -> None:
    """It generates the project files in the current directory."""
    result = runner.invoke(
        main,
        ["create", "--no-input", "--in-place", str(repository)],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    assert Path("README.md").read_text() == "# example\n"
    assert Path("post_gen_project").is_file()
    assert Path(".cookiecutter.json").is_file()


def test_directory(runner: CliRunner, repository: Path, tmp_path: Path) -> None:
    """It uses the template in the given subdirectory."""
    directory = "a"
    move_repository_files_to_subdirectory(repository, directory)

    result = runner.invoke(
        main,
        ["create", f"--directory={directory}", str(repository)],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert Path("example", "README.md").is_file()
