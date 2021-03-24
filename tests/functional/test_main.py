"""Test cases for the __main__ module."""
from collections.abc import Iterator
from pathlib import Path

import pygit2
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


@pytest.fixture
def repository(template_directory: Path) -> Path:
    """Fixture for a template repository."""
    repository = pygit2.init_repository(template_directory)
    signature = pygit2.Signature("you", "you@example.com")
    repository.index.add("cookiecutter.json")
    repository.index.add("{{ cookiecutter.project }}/README.md")
    tree = repository.index.write_tree()
    repository.create_commit(
        "HEAD",
        signature,
        signature,
        "Initial",
        tree,
        [],
    )
    return template_directory


def test_main_cookiecutter(runner: CliRunner, repository: Path) -> None:
    """It generates a project."""
    runner.invoke(
        __main__.main,
        [str(repository)],
        input="foobar\n\n\n",
        catch_exceptions=False,
    )
    assert Path("foobar", "README.md").read_text() == "# foobar\n"
