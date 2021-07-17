"""Functional tests for the cutty CLI."""
from importlib.metadata import version

from click.testing import CliRunner

from cutty.entrypoints.cli import main


def test_help(runner: CliRunner) -> None:
    """It exits with a status code of zero."""
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0


def test_version(runner: CliRunner) -> None:
    """It displays the version."""
    result = runner.invoke(main, ["--version"])
    assert version("cutty") in result.output
