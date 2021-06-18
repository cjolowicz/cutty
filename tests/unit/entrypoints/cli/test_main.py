"""Unit tests for cutty.entrypoints.cli.main."""
from click.testing import CliRunner

from cutty.entrypoints.cli import main


def test_help() -> None:
    """It exits with success."""
    result = CliRunner().invoke(main, ["--help"])
    assert result.exit_code == 0
