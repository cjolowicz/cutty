"""Fixtures for functional tests."""
from collections.abc import Iterator
from pathlib import Path

import pygit2
import pytest
from click.testing import CliRunner


@pytest.fixture
def runner() -> Iterator[CliRunner]:
    """Fixture for invoking command-line interfaces."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        yield runner


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
