"""Test fixtures."""
from pathlib import Path
from textwrap import dedent
from typing import Iterator

import pytest
from _pytest.monkeypatch import MonkeyPatch
from click.testing import CliRunner

from cutty import locations
from cutty.common import git


@pytest.fixture(scope="session", autouse=True)
def git_author() -> None:
    """Provide author information to git commit."""
    git.env.update(
        {
            "GIT_AUTHOR_NAME": "Example Author",
            "GIT_AUTHOR_EMAIL": "example.author@example.com",
            "GIT_COMMITTER_NAME": "Example Author",
            "GIT_COMMITTER_EMAIL": "example.author@example.com",
        }
    )


@pytest.fixture
def repository(tmp_path: Path) -> git.Repository:
    """Initialize repository in a temporary directory."""
    path = tmp_path / "repository"
    path.mkdir()
    return git.Repository.init(path)


@pytest.fixture
def user_cache_dir(monkeypatch: MonkeyPatch, tmp_path: Path) -> Path:
    """Replace the application cache directory by a temporary directory."""
    path = tmp_path / ".cache" / locations.cache.name
    path.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("appdirs.user_cache_dir", lambda *args, **kwargs: path)
    return path


@pytest.fixture
def runner() -> Iterator[CliRunner]:
    """Fixture for invoking command-line interfaces."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        yield runner


@pytest.fixture
def template(repository: git.Repository) -> git.Repository:
    """Set up a minimal template repository."""
    cookiecutter_json = """\
    {
      "project": "example"
    }
    """

    readme = """\
    # {{cookiecutter.project}}
    """

    (repository.path / "{{cookiecutter.project}}").mkdir()
    (repository.path / "{{cookiecutter.project}}" / ".cookiecutter.json").write_text(
        """{{cookiecutter | jsonify}}"""
    )
    (repository.path / "{{cookiecutter.project}}" / "README.md").write_text(
        dedent(readme)
    )
    (repository.path / "cookiecutter.json").write_text(dedent(cookiecutter_json))

    repository.add(".")
    repository.commit(message="Initial commit")
    repository.tag("v1.0.0")

    return repository
