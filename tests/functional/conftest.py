"""Fixtures for functional tests."""
import json
from collections.abc import Iterator
from pathlib import Path
from textwrap import dedent

import pygit2
import pytest
from click.testing import CliRunner

from cutty.filestorage.adapters.observers.git import commit as _commit


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

    template = tmp_path / "template"
    context = {
        "project": "example",
        "license": ["MIT", "GPL-3.0", "Apache-2.0"],
        "cli": True,
        "_extensions": ["jinja2_time.TimeExtension"],
    }

    create(template / "cookiecutter.json", json.dumps(context))

    create(
        template / "{{ cookiecutter.project }}" / "README.md",
        """
        # {{ cookiecutter.project }}
        """,
    )

    create(
        template / "{{ cookiecutter.project }}" / ".cookiecutter.json",
        """
        {{ cookiecutter | jsonify }}
        """,
    )

    create(
        template / "hooks" / "post_gen_project.py",
        """
        open("post_gen_project", mode="w")
        """,
    )

    return template


def commit(repository: pygit2.Repository, *, message: str) -> None:
    """Commit all changes in the repository."""
    signature = pygit2.Signature("you", "you@example.com")
    _commit(repository, message=message, signature=signature)


@pytest.fixture
def repository(template_directory: Path) -> Path:
    """Fixture for a template repository."""
    repository = pygit2.init_repository(template_directory)
    commit(repository, message="Initial")
    return template_directory


def move_repository_files_to_subdirectory(repositorypath: Path, directory: str) -> None:
    """Move all files in the repository to the given subdirectory."""
    repository = pygit2.Repository(repositorypath)
    builder = repository.TreeBuilder()
    builder.insert(directory, repository.head.peel().tree.id, pygit2.GIT_FILEMODE_TREE)
    tree = repository[builder.write()]
    repository.checkout_tree(tree)
    commit(repository, message=f"Move files to subdirectory {directory}")
