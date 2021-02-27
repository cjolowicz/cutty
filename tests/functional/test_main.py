"""Test cases for the __main__ module."""
from collections.abc import Iterator
from pathlib import Path

import pytest
from click.testing import CliRunner

from cutty import __main__


@pytest.fixture
def runner() -> Iterator[CliRunner]:
    """Fixture for invoking command-line interfaces."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        yield runner


def test_main_help(runner: CliRunner) -> None:
    """It exits with a status code of zero."""
    result = runner.invoke(__main__.main, ["--help"])
    assert result.exit_code == 0


def test_main_cookiecutter(runner: CliRunner, template_directory: Path) -> None:
    """It generates a project."""
    runner.invoke(
        __main__.main,
        [f"{template_directory}"],
        input="foobar\n\n",
        catch_exceptions=False,
    )
    assert Path("foobar", "README.md").read_text() == "# foobar\n"
