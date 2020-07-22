"""Test cases for the console module."""
from click.testing import CliRunner

from cutty.update import console


def test_help_succeeds(runner: CliRunner) -> None:
    """It exits with a status code of zero."""
    result = runner.invoke(console.update, ["--help"])
    assert result.exit_code == 0
