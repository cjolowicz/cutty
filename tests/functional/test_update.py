"""Functional tests for the update CLI."""
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
