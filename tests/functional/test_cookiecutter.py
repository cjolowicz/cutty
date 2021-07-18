"""Functional tests for the cookiecutter CLI."""
from click.testing import CliRunner

from cutty.entrypoints.cli import main


def test_create_help(runner: CliRunner) -> None:
    """It exits with a status code of zero."""
    result = runner.invoke(main, ["cookiecutter", "--help"])
    assert result.exit_code == 0
