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


def test_update(runner: CliRunner, repository: Path) -> None:
    """It applies changes from the template."""
    runner.invoke(
        main, ["create", "--no-input", str(repository)], catch_exceptions=False
    )

    # Update README.md.
    path = repository / "{{ cookiecutter.project }}" / "README.md"
    path.write_text(path.read_text() + "An awesome project.\n")

    # Commit the changes.
    commit(pygit2.Repository(repository), message="Update README.md")

    os.chdir("example")

    runner.invoke(main, ["update"], catch_exceptions=False)
    assert Path("README.md").read_text() == "# example\nAn awesome project.\n"
