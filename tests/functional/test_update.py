"""Functional tests for the update CLI."""
import json
import os
from pathlib import Path

import pygit2
from click.testing import CliRunner

from cutty.entrypoints.cli import main
from tests.functional.conftest import commit


def test_help(runner: CliRunner) -> None:
    """It exits with a status code of zero."""
    result = runner.invoke(main, ["update", "--help"])
    assert result.exit_code == 0


def test_update_trivial(runner: CliRunner, repository: Path) -> None:
    """It applies changes from the template."""
    runner.invoke(
        main,
        ["create", "--no-input", str(repository), "project=awesome"],
        catch_exceptions=False,
    )

    # Update README.md in the template.
    path = repository / "{{ cookiecutter.project }}" / "README.md"
    path.write_text(path.read_text() + "An awesome project.\n")
    commit(pygit2.Repository(repository), message="Update README.md")

    # Update the project.
    os.chdir("awesome")
    runner.invoke(main, ["update"], catch_exceptions=False)

    assert Path("README.md").read_text() == "# awesome\nAn awesome project.\n"


def test_update_merge(runner: CliRunner, repository: Path) -> None:
    """It merges changes from the template."""
    runner.invoke(
        main,
        ["create", "--no-input", str(repository), "project=awesome"],
        catch_exceptions=False,
    )

    projectdir = Path("awesome")

    # Update README.md in the project.
    path = projectdir / "README.md"
    path.write_text(path.read_text() + "An awesome project.\n")
    commit(pygit2.Repository(projectdir), message="Update README.md")

    # Add LICENSE in the template.
    path = repository / "{{ cookiecutter.project }}" / "LICENSE"
    path.touch()
    commit(pygit2.Repository(repository), message="Add LICENSE")

    # Update the project.
    os.chdir(projectdir)
    runner.invoke(main, ["update"], catch_exceptions=False)

    assert Path("README.md").read_text() == "# awesome\nAn awesome project.\n"
    assert Path("LICENSE").is_file()


def test_update_conflict(runner: CliRunner, repository: Path) -> None:
    """It exits with a non-zero status on merge conflicts."""
    runner.invoke(
        main,
        ["create", "--no-input", str(repository), "project=awesome"],
        catch_exceptions=False,
    )

    projectdir = Path("awesome")

    # Update README.md in the project.
    path = projectdir / "README.md"
    path.write_text(path.read_text() + "An awesome project.\n")
    commit(pygit2.Repository(projectdir), message="Update README.md")

    # Update README.md in the template.
    path = repository / "{{ cookiecutter.project }}" / "README.md"
    path.write_text(path.read_text() + "An excellent project.\n")
    commit(pygit2.Repository(repository), message="Update README.md")

    # Update the project.
    os.chdir(projectdir)
    result = runner.invoke(main, ["update"])

    assert result.exit_code != 0


def test_update_remove(runner: CliRunner, repository: Path) -> None:
    """It applies file deletions from the template."""
    runner.invoke(
        main,
        ["create", "--no-input", str(repository), "project=awesome"],
        catch_exceptions=False,
    )

    projectdir = Path("awesome")

    # Remove README in the template.
    path = repository / "{{ cookiecutter.project }}" / "README.md"
    path.unlink()
    commit(pygit2.Repository(repository), message="Remove README.md")

    # Update the project.
    os.chdir(projectdir)
    runner.invoke(main, ["update"], catch_exceptions=False)

    assert not Path("README.md").is_file()


def test_update_noop(runner: CliRunner, repository: Path) -> None:
    """It does nothing if the generated project did not change."""
    runner.invoke(
        main,
        ["create", "--no-input", str(repository), "project=awesome"],
        catch_exceptions=False,
    )

    projectdir = Path("awesome")
    project = pygit2.Repository(projectdir)
    oldhead = project.head.target

    os.chdir(projectdir)
    runner.invoke(main, ["update"], catch_exceptions=False)

    assert oldhead == project.head.target


def test_update_new_variables(runner: CliRunner, repository: Path) -> None:
    """It prompts for variables added after the last project generation."""
    runner.invoke(
        main,
        ["create", "--no-input", str(repository), "project=awesome"],
        catch_exceptions=False,
    )

    # Add project variable `status`.
    path = repository / "cookiecutter.json"
    data = json.loads(path.read_text())
    data["status"] = ["alpha", "beta", "stable"]
    path.write_text(json.dumps(data))
    commit(pygit2.Repository(repository), message="Add status variable")

    # Update the project.
    os.chdir("awesome")
    runner.invoke(main, ["update"], input="3\n", catch_exceptions=False)

    # Verify that the variable was bound by user input.
    path = Path(".cookiecutter.json")
    data = json.loads(path.read_text())
    assert "stable" == data["status"]


def test_update_extra_context_old_variable(runner: CliRunner, repository: Path) -> None:
    """It allows setting variables on the command-line."""
    runner.invoke(
        main,
        ["create", "--no-input", str(repository), "project=awesome"],
        catch_exceptions=False,
    )

    # Update the project.
    os.chdir("awesome")
    result = runner.invoke(
        main, ["update", "project=excellent"], catch_exceptions=False
    )
    assert result.exit_code == 0

    # Verify that the variable was bound.
    path = Path(".cookiecutter.json")
    data = json.loads(path.read_text())
    assert "excellent" == data["project"]


def test_update_extra_context_new_variable(runner: CliRunner, repository: Path) -> None:
    """It allows setting variables on the command-line."""
    runner.invoke(
        main,
        ["create", "--no-input", str(repository), "project=awesome"],
        catch_exceptions=False,
    )

    # Add project variable `status`.
    path = repository / "cookiecutter.json"
    data = json.loads(path.read_text())
    data["status"] = ["alpha", "beta", "stable"]
    path.write_text(json.dumps(data))
    commit(pygit2.Repository(repository), message="Add status variable")

    # Update the project.
    os.chdir("awesome")
    result = runner.invoke(main, ["update", "status=stable"], catch_exceptions=False)
    assert result.exit_code == 0

    # Verify that the variable was bound.
    path = Path(".cookiecutter.json")
    data = json.loads(path.read_text())
    assert "stable" == data["status"]


def test_update_no_input(runner: CliRunner, repository: Path) -> None:
    """It does not prompt for variables added after the last project generation."""
    runner.invoke(
        main,
        ["create", "--no-input", str(repository), "project=awesome"],
        catch_exceptions=False,
    )

    # Add project variable `status`.
    path = repository / "cookiecutter.json"
    data = json.loads(path.read_text())
    data["status"] = ["alpha", "beta", "stable"]
    path.write_text(json.dumps(data))
    commit(pygit2.Repository(repository), message="Add status variable")

    # Update the project.
    os.chdir("awesome")
    result = runner.invoke(
        main, ["update", "--no-input"], input="3\n", catch_exceptions=False
    )
    assert result.exit_code == 0

    # Verify that the variable was bound using the default.
    path = Path(".cookiecutter.json")
    data = json.loads(path.read_text())
    assert "alpha" == data["status"]


def test_update_rename_projectdir(runner: CliRunner, repository: Path) -> None:
    """It generates the project in the project directory irrespective of its name."""
    runner.invoke(
        main,
        ["create", "--no-input", str(repository), "project=awesome"],
        catch_exceptions=False,
    )

    # Rename the project directory.
    projectdir = Path("awesome")
    projectdir.rename("awesome2")

    # Update README.md in the template.
    path = repository / "{{ cookiecutter.project }}" / "README.md"
    path.write_text(path.read_text() + "An awesome project.\n")
    commit(pygit2.Repository(repository), message="Update README.md")

    # Update the project.
    os.chdir("awesome2")
    runner.invoke(main, ["update"], catch_exceptions=False)

    # Verify that the README was updated.
    assert Path("README.md").read_text() == "# awesome\nAn awesome project.\n"


def test_update_cwd(runner: CliRunner, repository: Path) -> None:
    """It updates the project in the specified directory."""
    runner.invoke(
        main,
        ["create", "--no-input", str(repository), "project=awesome"],
        catch_exceptions=False,
    )

    # Update README.md in the template.
    path = repository / "{{ cookiecutter.project }}" / "README.md"
    path.write_text(path.read_text() + "An awesome project.\n")
    commit(pygit2.Repository(repository), message="Update README.md")

    # Update the project.
    projectdir = Path("awesome")
    runner.invoke(main, ["update", f"--cwd={projectdir}"], catch_exceptions=False)

    assert (projectdir / "README.md").read_text() == "# awesome\nAn awesome project.\n"
