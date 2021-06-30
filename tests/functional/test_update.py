"""Functional tests for the update CLI."""
from click.testing import CliRunner

from cutty.entrypoints.cli import main


def test_help(runner: CliRunner) -> None:
    """It exits with a status code of zero."""
    result = runner.invoke(main, ["update", "--help"])
    assert result.exit_code == 0
