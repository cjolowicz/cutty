"""Fixtures for functional tests."""
import json
from collections.abc import Iterator
from pathlib import Path
from textwrap import dedent

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
def template_directory(tmp_path: Path) -> Path:
    """Fixture for a template directory."""

    def create(path: Path, text: str) -> None:
        """Create a file with the given path and contents."""
        text = dedent(text).removeprefix("\n")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    context = {
        "project": "example",
        "license": ["MIT", "GPL-3.0", "Apache-2.0"],
        "cli": True,
        "_extensions": ["jinja2_time.TimeExtension"],
    }

    create(tmp_path / "cookiecutter.json", json.dumps(context))

    create(
        tmp_path / "{{ cookiecutter.project }}" / "README.md",
        """
        # {{ cookiecutter.project }}
        """,
    )

    create(
        tmp_path / "hooks" / "post_gen_project.py",
        """
        open("post_gen_project", mode="w")
        """,
    )

    return tmp_path


def commit(repository: pygit2.Repository, *, message: str) -> None:
    """Commit all changes."""
    signature = pygit2.Signature("you", "you@example.com")
    repository.index.add("cookiecutter.json")
    repository.index.add("{{ cookiecutter.project }}/README.md")
    repository.index.add("hooks/post_gen_project.py")
    tree = repository.index.write_tree()
    repository.create_commit(
        "HEAD",
        signature,
        signature,
        message,
        tree,
        [],
    )


@pytest.fixture
def repository(template_directory: Path) -> Path:
    """Fixture for a template repository."""
    repository = pygit2.init_repository(template_directory)
    commit(repository, message="Initial")
    return template_directory
