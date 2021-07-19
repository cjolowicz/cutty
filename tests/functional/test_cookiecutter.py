"""Functional tests for the cookiecutter CLI."""
from pathlib import Path

import pygit2
from click.testing import CliRunner

from cutty.entrypoints.cli import main
from tests.functional.conftest import commit
from tests.functional.conftest import move_repository_files_to_subdirectory


def test_create_help(runner: CliRunner) -> None:
    """It exits with a status code of zero."""
    result = runner.invoke(main, ["cookiecutter", "--help"])
    assert result.exit_code == 0


def test_create_cookiecutter(runner: CliRunner, repository: Path) -> None:
    """It generates a project."""
    runner.invoke(
        main,
        ["cookiecutter", str(repository)],
        input="foobar\n\n\n",
        catch_exceptions=False,
    )
    assert Path("foobar", "README.md").read_text() == "# foobar\n"
    assert Path("foobar", "post_gen_project").is_file()
    assert Path("foobar", ".cookiecutter.json").is_file()


def test_no_input(runner: CliRunner, repository: Path) -> None:
    """It does not prompt for variables."""
    runner.invoke(
        main,
        ["cookiecutter", "--no-input", str(repository)],
        catch_exceptions=False,
    )

    assert Path("example", "README.md").is_file()


def test_extra_context(runner: CliRunner, repository: Path) -> None:
    """It allows setting variables on the command-line."""
    runner.invoke(
        main,
        ["cookiecutter", str(repository), "project=awesome"],
        catch_exceptions=False,
    )

    assert Path("awesome", "README.md").is_file()


def test_checkout(runner: CliRunner, repository: Path) -> None:
    """It uses the specified revision of the template."""
    initial = pygit2.Repository(repository).head.target

    # Add LICENSE to the template.
    path = repository / "{{ cookiecutter.project }}" / "LICENSE"
    path.touch()
    commit(pygit2.Repository(repository), message="Add LICENSE")

    result = runner.invoke(
        main,
        ["cookiecutter", f"--checkout={initial}", str(repository)],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert not Path("example", "LICENSE").exists()


def test_output_dir(runner: CliRunner, repository: Path, tmp_path: Path) -> None:
    """It generates the project under the specified directory."""
    outputdir = tmp_path / "outputdir"
    result = runner.invoke(
        main,
        ["cookiecutter", f"--output-dir={outputdir}", str(repository)],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert (outputdir / "example" / "README.md").is_file()


def test_directory(runner: CliRunner, repository: Path, tmp_path: Path) -> None:
    """It uses the template in the given subdirectory."""
    directory = "a"
    move_repository_files_to_subdirectory(repository, directory)

    result = runner.invoke(
        main,
        ["cookiecutter", f"--directory={directory}", str(repository)],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert Path("example", "README.md").is_file()


def test_overwrite(runner: CliRunner, repository: Path) -> None:
    """It overwrites existing files."""
    Path("example").mkdir()
    Path("example", "README.md").touch()

    result = runner.invoke(
        main,
        ["cookiecutter", "--overwrite-if-exists", str(repository)],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert Path("example", "README.md").read_text() == "# example\n"
