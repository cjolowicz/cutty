"""Functional tests for the create CLI."""
from pathlib import Path

from click.testing import CliRunner

from cutty.entrypoints.cli import main


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
