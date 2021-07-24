"""Fixtures for functional tests."""
import json
from collections.abc import Iterator
from pathlib import Path
from textwrap import dedent
from typing import Optional
from typing import Protocol

import pygit2
import pytest
from click.testing import CliRunner

from cutty.entrypoints.cli import main
from tests.util.git import commit


@pytest.fixture
def runner() -> Iterator[CliRunner]:
    """Fixture for invoking command-line interfaces."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        yield runner


class RunCutty(Protocol):
    """Invoke the cutty CLI."""

    def __call__(self, *args: str, input: Optional[str] = None) -> str:
        """Invoke the cutty CLI."""


@pytest.fixture
def runcutty(runner: CliRunner) -> RunCutty:
    """Fixture for invoking the cutty CLI."""

    def _run(*args: str, input: Optional[str] = None) -> str:
        result = runner.invoke(main, args, input=input, catch_exceptions=False)

        if result.exit_code != 0:
            raise RuntimeError(result)

        return result.output

    return _run


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
        template / "hooks" / "post_gen_project.py",
        """
        open("post_gen_project", mode="w")
        """,
    )

    return template


@pytest.fixture
def template(template_directory: Path) -> Path:
    """Fixture for a template repository."""
    pygit2.init_repository(template_directory)
    commit(template_directory, message="Initial")
    return template_directory
