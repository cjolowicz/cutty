"""Functional tests for the create CLI."""
from collections.abc import Iterator
from pathlib import Path

import pygit2
import pytest
from click.testing import CliRunner

from cutty.entrypoints.cli import main


@pytest.fixture
def runner() -> Iterator[CliRunner]:
    """Fixture for invoking command-line interfaces."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        yield runner


def test_create_help(runner: CliRunner) -> None:
    """It exits with a status code of zero."""
    result = runner.invoke(main, ["create", "--help"])
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


def test_create_cookiecutter(runner: CliRunner, repository: Path) -> None:
    """It generates a project."""
    runner.invoke(
        main, ["create", str(repository)], input="foobar\n\n\n", catch_exceptions=False
    )
    assert Path("foobar", "README.md").read_text() == "# foobar\n"


def test_create_repository(runner: CliRunner, repository: Path) -> None:
    """It creates a git repository."""
    runner.invoke(
        main, ["create", str(repository)], input="foobar\n\n\n", catch_exceptions=False
    )
    project = pygit2.Repository("foobar")
    assert not project.head_is_unborn
